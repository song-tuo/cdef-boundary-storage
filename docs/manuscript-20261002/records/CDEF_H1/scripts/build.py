from common import *
import sys,concurrent.futures

def build(v,profile):
 src=ROOT/'src'/v;b=ROOT/'builds'/f'{v}_{profile}';tag=f'build_{v}_{profile}'
 args=['cmake','-S',src,'-B',b,'-DCMAKE_POLICY_VERSION_MINIMUM=3.5','-DENABLE_DOCS=OFF','-DCONFIG_LIBYUV=0','-DCONFIG_WEBM_IO=0','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_BUILD_TYPE='+('Release' if profile=='release' else 'Debug')]
 san={'asan':'address,undefined','tsan':'thread'}.get(profile)
 if san:args+=['-DSANITIZE='+san]
 for stage,cmd in [('configure',args),('compile',['cmake','--build',b,'-j','6'])]:
  r=run(tag+'_'+stage,cmd)
  if r['exit_code']:return r
 harnesses=['ivf_gate','ivf_recovery','ivf_recreate']
 for h in harnesses:
  cmd=['clang','-O2','-g','-Wno-deprecated-declarations','-I'+str(src),ROOT/'scripts'/(h+'.c'),b/'libaom.a','-lm','-lpthread','-o',b/h]
  if san:cmd+=['-fsanitize='+san,'-fno-omit-frame-pointer']
  r=run(tag+'_'+h,cmd)
  if r['exit_code']:return r
 return {'variant':v,'profile':profile,'exit_code':0}
if __name__=='__main__':
 tasks=[tuple(x.split(':')) for x in sys.argv[1:]]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:r=list(pool.map(lambda x:build(*x),tasks))
 save(ROOT/'results'/('build_batch_'+str(int(time.time()))+'.json'),r)
 sys.exit(int(any(x['exit_code'] for x in r)))
