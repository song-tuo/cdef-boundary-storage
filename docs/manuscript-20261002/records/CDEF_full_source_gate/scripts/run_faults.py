from pathlib import Path
import json, subprocess, os, time, sys
root=Path(__file__).resolve().parents[1];rows=[]
profile=sys.argv[1] if len(sys.argv)>1 else 'asan'
env0=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',TSAN_OPTIONS='halt_on_error=1')
def run(bin,stream,w,extra,tag):
    cmd=[str(root/'builds'/bin/'ivf_gate'),str(root/'testdata/generated'/(stream+'.ivf')),str(w),'1']
    try:p=subprocess.run(cmd,capture_output=True,text=True,timeout=30,env=dict(env0,**extra));code=p.returncode;stdout=p.stdout;stderr=p.stderr
    except subprocess.TimeoutExpired as e:code='TIMEOUT';stdout=e.stdout or '';stderr=e.stderr or '';stdout=stdout.decode() if isinstance(stdout,bytes) else stdout;stderr=stderr.decode() if isinstance(stderr,bytes) else stderr
    (root/'logs'/(tag+'.log')).write_text(stdout+stderr)
    output=json.loads(stdout) if stdout.strip().startswith('{') else {}
    bad=any(x in stderr for x in ['ERROR: AddressSanitizer','runtime error:','SUMMARY: ThreadSanitizer','Assertion failed','CDEF token exhaustion'])
    events=[]
    for line in stderr.splitlines():
        if line.startswith('{'):
            try:events.append(json.loads(line))
            except ValueError:pass
    return dict(exit=code,output=output,events=events,sanitizer_or_invariant_error=bad)
for stream in ['odd_8_420','odd_10_444','odd_12_422']:
    for w in [2,4,8,16]:
        ref=run('type_fix_release',stream,w,{},f'fault_ref_{stream}_{w}')
        assert ref['exit']==0
        cases=[(f'stage{s}',{'CDEF_GATE_FAULT_STAGE':str(s)}) for s in range(1,8)]
        cases += [(f'alloc_plane{p}',{'CDEF_GATE_ALLOC_PLANE':str(p)}) for p in range(3)]
        cases += [('alloc_owner',{'CDEF_GATE_ALLOC_OWNER':'1'}),('negative_stage',{'CDEF_GATE_FAULT_STAGE':'99'}),('negative_row',{'CDEF_GATE_FAULT_STAGE':'2','CDEF_GATE_FAULT_ROW':'9999'})]
        for name,env in cases:
            tag=f'fault_{profile}_{stream}_{w}_{name}';r=run('token_audit_'+profile,stream,w,env,tag)
            negative=name.startswith('negative')
            ok=r['exit']==(0 if negative else 3) and r['output'].get('destroy_status')==0 and not r['sanitizer_or_invariant_error']
            ok &= sum(x.get('event')=='cdef_pool_freed' for x in r['events'])==1
            if name.startswith('stage'):ok &= sum(x.get('event')=='fault' for x in r['events'])==1
            if name.startswith('alloc'):ok &= r['output'].get('status')==2 # AOM_CODEC_MEM_ERROR
            clean=run('token_audit_'+profile,stream,w,{},tag+'_clean_after')
            ok &= clean['exit']==0 and clean['output'].get('pixel_sha256')==ref['output']['pixel_sha256'] and clean['output'].get('output_frames')==ref['output']['output_frames']
            rows.append(dict(workload=stream,threads=w,case=name,fault=r,clean_after=clean,pass_gate=bool(ok)))
            (root/'results'/('fault_injection.json' if profile=='asan' else 'fault_injection_'+profile+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
            if not ok:raise RuntimeError(tag+' FAILED; evidence preserved')
        print(stream,w,'13 cases PASS',flush=True)
print('PASS',len(rows),'fault/control runs and',len(rows),'clean-after runs',flush=True)
