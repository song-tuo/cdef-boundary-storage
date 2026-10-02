from pathlib import Path
import subprocess,json,os,re,hashlib
root=Path(__file__).resolve().parents[1];rows=[]
for direction in ['sizeup','sizedown']:
    expected=[x.split()[0] for x in (root/'testdata'/f'av1-1-b8-03-{direction}.mkv.md5').read_text().splitlines() if x.strip()]
    ivf=root/'testdata/generated'/f'conformance_{direction}.ivf'
    for threads in [1,2,4,8,16]:
        for mt in [0,1]:
            for variant in ['baseline_release','type_fix_release','token_release','token_asan','token_tsan']:
                cmd=[str(root/'builds'/variant/'aomdec'),'--md5','--rawvideo','--output=frame-%4.raw',f'--threads={threads}',f'--row-mt={mt}',str(ivf)]
                p=subprocess.run(cmd,capture_output=True,text=True,timeout=90,env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',TSAN_OPTIONS='halt_on_error=1'))
                name=f'mkv_{direction}_{variant}_{threads}_{mt}'
                (root/'logs'/(name+'.log')).write_text(p.stdout+p.stderr)
                actual=[l.split()[0] for l in p.stdout.splitlines() if re.match(r'^[0-9a-f]{32} ',l)]
                ok=p.returncode==0 and actual==expected
                rows.append(dict(workload=direction,variant=variant,threads=threads,row_mt=mt,exit=p.returncode,frames=len(actual),pass_gate=ok,ivf_sha256=hashlib.sha256(ivf.read_bytes()).hexdigest()))
                (root/'results/mkv_conformance.json').write_text(json.dumps(rows,indent=2)+'\n')
                if not ok:raise RuntimeError(name+' FAILED')
    print(direction,'50 runs PASS',flush=True)
