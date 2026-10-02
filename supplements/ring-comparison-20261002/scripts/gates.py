from pathlib import Path
import json,subprocess,os,time,concurrent.futures,hashlib,re
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'CDEF_full_source_gate';NAT=ROOT.parent/'CDEF_paper_pipeline/revision_20260930/natural'
expected={ (r['workload'],r['threads'],r['row_mt']):r['output'] for r in json.loads((OLD/'results/correctness_release.json').read_text()) if r['variant']=='token'}
na=[json.loads(x) for x in (NAT/'results/correctness_allocation.jsonl').read_text().splitlines()]
NEXP={(r['stream'],r['workers']):r['output'] for r in na}
resultfile=ROOT/'results/gates.jsonl';assert not resultfile.exists()
env={k:v for k,v in os.environ.items() if not k.startswith(('CDEF_','ASAN_OPTIONS','TSAN_OPTIONS','UBSAN_OPTIONS'))}
env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',TSAN_OPTIONS='halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
def run(name,build,inp,w,mt,exp,extra=None,fault=False,recovery=False):
 e=env.copy();e.update(extra or {});exe='ivf_recovery' if recovery else 'ivf_gate';cmd=[str(ROOT/'builds'/build/exe),str(inp),str(w),str(mt)];start=time.time()
 try:p=subprocess.run(cmd,env=e,capture_output=True,text=True,timeout=120);out=p.stdout;err=p.stderr;rc=p.returncode
 except subprocess.TimeoutExpired as x:out=x.stdout or b'';err=x.stderr or b'';rc='TIMEOUT';out=out.decode(errors='replace') if isinstance(out,bytes) else out;err=err.decode(errors='replace') if isinstance(err,bytes) else err
 stem=ROOT/'logs'/name;stem.with_suffix('.stdout').write_text(out);stem.with_suffix('.stderr').write_text(err)
 rec=dict(id=name,build=build,command=cmd,extra_environment=extra or {},start=start,end=time.time(),exit_code=rc,fault=fault,recovery=recovery)
 try:obs=json.loads(out);rec['output']=obs
 except Exception:obs={}
 bad=bool(re.search(r'ERROR: AddressSanitizer|runtime error:|WARNING: ThreadSanitizer|ThreadSanitizer: reported|Assertion .*failed',err))
 if fault and not recovery:ok=rc==3 and obs.get('status',0)!=0 and obs.get('destroy_status')==0 and 'CDEF pool test fault' in err and not bad
 else:ok=rc==0 and not bad and all(obs.get(k)==exp[k] for k in ['pixel_sha256','output_frames','output_bytes','status','destroy_status'])
 if recovery:ok=ok and err.count('same_instance_recovery')==1
 events=[json.loads(l) for l in err.splitlines() if l.startswith('{"event":"cdef_pool_diag"')]
 if events:
  rec['activity']={'frames':len(events),'dispatch_rows':sum(x['dispatch_rows'] for x in events),'wait_rows':sum(x['wait_rows'] for x in events),'wait_calls':sum(x['wait_calls'] for x in events),'worker_wait_ns':sum(x['worker_wait_ns'] for x in events),'allocation_values':sorted({x['requested_bytes'] for x in events})}
  if inp.name.endswith('3840x2160_first60.ivf') and not fault:
   ok=ok and len(events)==60 and all(x['workers']==w and x['requested_bytes']==min(66,2*w+1)*30720 for x in events)
  if extra and 'CDEF_POOL_HOLD_ROW' in extra and not fault and build.startswith('ring'):
   ok=ok and rec['activity']['wait_calls']>0
 rec['pass']=ok
 with resultfile.open('a') as f:f.write(json.dumps(rec)+'\n')
 if not ok:raise RuntimeError(json.dumps(rec))
 return rec
# Fresh recovery harness only clears supplemental test controls after its first error.
s=(OLD/'scripts/ivf_recovery.c').read_text().replace('unsetenv("CDEF_GATE_ALLOC_PLANE"); unsetenv("CDEF_GATE_ALLOC_OWNER");','unsetenv("CDEF_GATE_ALLOC_PLANE"); unsetenv("CDEF_GATE_ALLOC_OWNER"); unsetenv("CDEF_POOL_FAULT_ROW"); unsetenv("CDEF_POOL_HOLD_ROW"); unsetenv("CDEF_POOL_HOLD_MS");')
(ROOT/'scripts/ivf_recovery.c').write_text(s)
for profile,san in [('diag',None),('asan','address,undefined'),('tsan','thread')]:
 cmd=['clang','-O2','-g','-Wno-deprecated-declarations','-I'+str(ROOT/'src/ring'),str(ROOT/'scripts/ivf_recovery.c'),str(ROOT/'builds'/('ring_'+profile)/'libaom.a'),'-lm','-lpthread','-o',str(ROOT/'builds'/('ring_'+profile)/'ivf_recovery')]+(['-fsanitize='+san,'-fno-omit-frame-pointer'] if san else [])
 subprocess.run(cmd,check=True,capture_output=True)
# Small synthetic inputs can safely run concurrently; they are correctness only.
jobs=[]
for (stream,w,mt),exp in expected.items():
 for v in ['token_release','ring_release']:
  jobs.append((f'normal_{v}_{stream}_w{w}_m{mt}',v,OLD/'testdata/generated'/f'{stream}.ivf',w,mt,exp))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda x:run(*x),jobs))
print('normal synthetic',len(jobs),'PASS',flush=True)
# Sanitizer coverage: all 18 synthetic inputs at 8 and 16 workers, row-MT enabled.
for profile in ['asan','tsan']:
 for (stream,w,mt),exp in expected.items():
  if w in [8,16] and mt==1:run(f'{profile}_{stream}_w{w}', 'ring_'+profile, OLD/'testdata/generated'/f'{stream}.ivf',w,mt,exp)
 print(profile,'synthetic 36 PASS',flush=True)
for scene in ['Beauty','Jockey','HoneyBee']:
 stream=scene+'_3840x2160_first60';inp=NAT/'media'/f'{stream}.ivf'
 for w in [8,16]:
  exp=NEXP[(stream,w)]
  for build in ['token_release','ring_release','token_diag','ring_diag','ring_asan','ring_tsan']:
   run(f'natural_{scene}_w{w}_{build}',build,inp,w,1,exp)
  print('natural',scene,w,'PASS',flush=True)
# Slow consumer and error paths on a short retained synthetic stream.
stream='odd_8_420';inp=OLD/'testdata/generated'/f'{stream}.ivf'
# Need more frame rows than workers for deliberate capacity collisions: use 4K stream.
stream='Beauty_3840x2160_first60';inp=NAT/'media'/f'{stream}.ivf'
for profile in ['diag','asan','tsan']:
 for w in [8,16]:
  exp=NEXP[(stream,w)];extra={'CDEF_POOL_HOLD_ROW':'1','CDEF_POOL_HOLD_MS':'30'}
  run(f'slow_w{w}_{profile}','ring_'+profile,inp,w,1,exp,extra)
  extra={**extra,'CDEF_POOL_FAULT_ROW':'1'}
  run(f'fault_w{w}_{profile}','ring_'+profile,inp,w,1,exp,extra,fault=True)
  run(f'recovery_w{w}_{profile}','ring_'+profile,inp,w,1,exp,extra,fault=True,recovery=True)
 print(profile,'slow/fault/recovery PASS',flush=True)
rows=[json.loads(x) for x in resultfile.read_text().splitlines()];assert all(x['pass'] for x in rows)
(ROOT/'results/GATES_PASS.json').write_text(json.dumps({'passed':len(rows),'new_timing_campaign_started':False,'groups':{'synthetic_release':360,'synthetic_sanitizers':72,'natural':36,'stress_fault_recovery':18}},indent=2)+'\n')
print('ALL GATES PASS',len(rows),flush=True)
