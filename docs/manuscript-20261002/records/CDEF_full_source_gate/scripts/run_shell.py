from pathlib import Path
import subprocess,os,json,shutil
root=Path(__file__).resolve().parents[1]
shim=root/'scripts/tarball_no_git';shim.mkdir(exist_ok=True)
git=shim/'git';git.write_text('#!/bin/sh\n# Upstream source_version() must use CMake version for a source tarball.\nexit 127\n');git.chmod(0o755)
rows=[]
for v in ['baseline','type_fix','token']:
    log=root/'logs'/f'shell_aomdec_{v}.log'
    if log.exists():shutil.copy2(log,log.with_suffix('.attempt1.log'))
    b=root/'builds'/f'{v}_release';d=root/'results'/f'shell_{v}';d.mkdir(exist_ok=True)
    c=['sh',str(root/'src'/v/'test/aomdec.sh'),'--bin-path',str(b),'--config-path',str(b),'--test-data-path',str(root/'testdata'),'--show-program-output','--verbose']
    with log.open('w') as f:p=subprocess.run(c,cwd=d,stdout=f,stderr=f,env=dict(os.environ,PATH=str(shim)+':'+os.environ['PATH']),timeout=600)
    rows.append(dict(variant=v,exit=p.returncode,command=c,tarball_version_workaround=str(git)))
    (root/'results/shell_decode.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(v,p.returncode,flush=True)
