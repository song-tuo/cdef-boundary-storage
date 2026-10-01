from pathlib import Path
import subprocess, sys, json, time
root=Path(__file__).resolve().parents[1]
variant=sys.argv[1]; profile=sys.argv[2]
src=root/'src'/variant; build=root/'builds'/f'{variant}_{profile}'
args=['cmake','-S',str(src),'-B',str(build),'-DCMAKE_POLICY_VERSION_MINIMUM=3.5','-DENABLE_DOCS=OFF','-DCONFIG_LIBYUV=0','-DCONFIG_WEBM_IO=0','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
args+=['-DCMAKE_BUILD_TYPE='+('Release' if profile=='release' else 'Debug')]
san={'asan':'address,undefined','tsan':'thread'}.get(profile)
if san: args+=['-DSANITIZE='+san]
record={'variant':variant,'profile':profile,'configure':args,'started':time.time()}
for stage,cmd in [('configure',args),('build',['cmake','--build',str(build),'-j','6'])]:
    with (root/'logs'/f'{variant}_{profile}.{stage}.log').open('w') as f:
        p=subprocess.run(cmd,stdout=f,stderr=f)
    record[stage+'_exit']=p.returncode
    if p.returncode: break
else:
    cmd=['clang','-O2','-g','-Wno-deprecated-declarations','-I'+str(src),str(root/'scripts/ivf_gate.c'),str(build/'libaom.a'),'-lm','-lpthread','-o',str(build/'ivf_gate')]
    if san: cmd+=['-fsanitize='+san,'-fno-omit-frame-pointer']
    with (root/'logs'/f'{variant}_{profile}.harness.log').open('w') as f: record['harness_exit']=subprocess.run(cmd,stdout=f,stderr=f).returncode
record['finished']=time.time()
(root/'results'/f'build_{variant}_{profile}.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
sys.exit(max(record.get(k,0) for k in ['configure_exit','build_exit','harness_exit']))
