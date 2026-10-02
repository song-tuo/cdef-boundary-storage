from common import *
import concurrent.futures
jobs=[('type_fix','release'),('dual_token','release'),('hybrid','release'),('type_fix_audit','release'),('dual_token_audit','release'),('hybrid_audit','release'),('hybrid_audit','asan'),('hybrid_audit','tsan'),('type_fix_account','release'),('dual_token_account','release'),('hybrid_account','release')]
def job(x):
 v,profile=x;b=ROOT/'builds'/f'{v}_{profile}';tag=f'rebuild2_{v}_{profile}';r=run(tag+'_library',['cmake','--build',b,'-j','6'])
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
