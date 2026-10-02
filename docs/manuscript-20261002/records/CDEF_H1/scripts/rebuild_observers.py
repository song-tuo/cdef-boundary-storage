from common import *
import concurrent.futures
jobs=[('type_fix','release'),('dual_token','release'),('hybrid','release'),('type_fix_audit','release'),('dual_token_audit','release'),('hybrid_audit','release'),('hybrid_audit','asan'),('hybrid_audit','tsan'),('type_fix_account','release'),('dual_token_account','release'),('hybrid_account','release')]
for v in ['dual_token','hybrid']:
 p=ROOT/'src'/(v+'_audit')/'av1/common/thread_common.c';s=p.read_text()
 s=s.replace('    h1_row_finish(cdef_sync,cur_fbr);\n','')
 anchor='  // Incoming top is produced by row-1 and consumed through the END of this'
 ins='''  if(!sync->cdef_row_mt[row].gate_active)h1_violation("double_release",row);
  sync->cdef_row_mt[row].gate_active=0;
  fprintf(stderr,"{\\"h1\\":\\"release\\",\\"row\\":%d}\\n",row);
'''
 assert s.count(anchor)==1;s=s.replace(anchor,ins+anchor);p.write_text(s)
def job(x):
 v,profile=x;b=ROOT/'builds'/f'{v}_{profile}';tag=f'rebuild_{v}_{profile}';r=run(tag+'_library',['cmake','--build',b,'-j','6'])
 if r['exit_code']:return r
 for h in ['ivf_gate','ivf_recovery','ivf_recreate']:
  cmd=['clang','-O2','-g','-Wno-deprecated-declarations','-I'+str(ROOT/'src'/v),ROOT/'scripts'/(h+'.c'),b/'libaom.a','-lm','-lpthread','-o',b/h]
  if profile in ['asan','tsan']:cmd+=['-fsanitize='+{'asan':'address,undefined','tsan':'thread'}[profile],'-fno-omit-frame-pointer']
  r=run(tag+'_'+h,cmd)
  if r['exit_code']:return r
 return {'variant':v,'profile':profile,'exit_code':0}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(job,jobs))
save(ROOT/'results/observer_builds.json',r)
assert all(not x['exit_code'] for x in r)
