"""Same codec instance: inject, re-submit keyframe, decode, then destroy."""
from pathlib import Path
import subprocess,json,os,sys
root=Path(__file__).resolve().parents[1];profile=sys.argv[1]
source=(root/'scripts/ivf_gate.c').read_text()
source=source.replace('uint64_t decode_ns=0,frames=0,bytes=0,decoded_packets=0;', 'unsigned recoveries=0;\n  uint64_t decode_ns=0,frames=0,bytes=0,decoded_packets=0;')
old='if(status) { fprintf(stderr,"codec_error=%d detail=%s\\n",status,aom_codec_error_detail(&ctx)?aom_codec_error_detail(&ctx):aom_codec_error(&ctx)); break; }'
new='''if(status) {
      fprintf(stderr,"codec_error=%d detail=%s\\n",status,aom_codec_error_detail(&ctx)?aom_codec_error_detail(&ctx):aom_codec_error(&ctx));
      if (!recoveries && i<count) {
        ++recoveries; status=0; frames=bytes=decoded_packets=0;
        CC_SHA256_Init(&hash);
        unsetenv("CDEF_GATE_ALLOC_PLANE"); unsetenv("CDEF_GATE_ALLOC_OWNER");
        fprintf(stderr,"{\\"event\\":\\"same_instance_recovery\\"}\\n");
        i=SIZE_MAX; continue;
      }
      break;
    }'''
assert old in source;source=source.replace(old,new)
src=root/'scripts/ivf_recovery.c';src.write_text(source)
b=root/'builds'/f'token_audit_{profile}';exe=b/'ivf_recovery'
cmd=['clang','-O2','-g','-Wno-deprecated-declarations','-I'+str(root/'src/token_audit'),str(src),str(b/'libaom.a'),'-lm','-lpthread','-o',str(exe)]
if profile in ['asan','tsan']:cmd+=['-fsanitize='+{'asan':'address,undefined','tsan':'thread'}[profile],'-fno-omit-frame-pointer']
subprocess.run(cmd,check=True);results=[]
for stream in ['odd_8_420','odd_10_444','odd_12_422']:
    for w in [2,8,16]:
        input=str(root/'testdata/generated'/(stream+'.ivf'))
        ref=json.loads(subprocess.check_output([str(root/'builds/type_fix_release/ivf_gate'),input,str(w),'1'],text=True))
        cases=[(f'stage{i}',{'CDEF_GATE_FAULT_STAGE':str(i)}) for i in range(1,8)]
        cases += [(f'plane{i}',{'CDEF_GATE_ALLOC_PLANE':str(i)}) for i in range(3)]+[('owner',{'CDEF_GATE_ALLOC_OWNER':'1'})]
        for label,extra in cases:
            env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',TSAN_OPTIONS='halt_on_error=1',**extra)
            p=subprocess.run([str(exe),input,str(w),'1'],capture_output=True,text=True,env=env,timeout=30)
            stem=f'recovery_{profile}_{stream}_{w}_{label}';(root/'logs'/(stem+'.log')).write_text(p.stdout+p.stderr)
            o=json.loads(p.stdout) if p.stdout.strip().startswith('{') else {}
            ok=p.returncode==0 and o.get('pixel_sha256')==ref['pixel_sha256'] and o.get('output_frames')==ref['output_frames'] and p.stderr.count('same_instance_recovery')==1 and o.get('destroy_status')==0
            results.append(dict(workload=stream,threads=w,case=label,exit=p.returncode,output=o,pass_gate=ok))
            (root/'results'/f'same_instance_recovery_{profile}.json').write_text(json.dumps(results,indent=2)+'\n')
            if not ok:raise RuntimeError(stem+' FAILED')
        print(profile,stream,w,'PASS',flush=True)
