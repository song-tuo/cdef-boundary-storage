from pathlib import Path
import subprocess,sys,time,json,concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
def build(variant,profile):
 name=variant+'_'+profile;src=ROOT/'src'/variant;dest=ROOT/'builds'/name
 diag=profile!='release';san={'asan':'address,undefined','tsan':'thread'}.get(profile)
 args=['cmake','-S',str(src),'-B',str(dest),'-DCMAKE_POLICY_VERSION_MINIMUM=3.5','-DENABLE_DOCS=OFF','-DCONFIG_LIBYUV=0','-DCONFIG_WEBM_IO=0','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_BUILD_TYPE='+('Debug' if san else 'Release')]
 if diag: args+=['-DCMAKE_C_FLAGS=-DCDEF_POOL_DIAGNOSTICS=1','-DCMAKE_CXX_FLAGS=-DCDEF_POOL_DIAGNOSTICS=1']
 if san: args+=['-DSANITIZE='+san]
 commands=[args,['cmake','--build',str(dest),'--target','aom','-j','6']]
 commands.append(['clang','-O2','-g','-Wno-deprecated-declarations','-I'+str(src),str(ROOT/'scripts/ivf_gate.c'),str(dest/'libaom.a'),'-lm','-lpthread','-o',str(dest/'ivf_gate')]+(['-fsanitize='+san,'-fno-omit-frame-pointer'] if san else []))
 rec={'build':name,'commands':commands,'start':time.time(),'results':[]}
 for i,cmd in enumerate(commands):
  with (ROOT/'logs'/f'build_{name}_{i}.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=f)
  rec['results'].append(r.returncode)
  if r.returncode:break
 rec['end']=time.time();(ROOT/'results'/f'build_{name}.json').write_text(json.dumps(rec,indent=2)+'\n')
 print(name,rec['results'],round(rec['end']-rec['start'],1),flush=True)
 return max(rec['results'])
if __name__=='__main__':
 jobs=[('token','release'),('ring','release'),('token','diag'),('ring','diag'),('ring','asan'),('ring','tsan')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rc=list(pool.map(lambda x:build(*x),jobs))
 sys.exit(max(rc))
