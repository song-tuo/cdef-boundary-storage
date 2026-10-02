from pathlib import Path
import subprocess,os,json,re
root=Path(__file__).resolve().parents[1];results=[]
for stream in ['odd_8_420','odd_10_444','odd_12_422']:
    cases=[('clean',{})]+[(f'stage{i}',{'CDEF_GATE_FAULT_STAGE':str(i)}) for i in range(1,8)]
    cases += [(f'plane{i}',{'CDEF_GATE_ALLOC_PLANE':str(i)}) for i in range(3)]+[('owner',{'CDEF_GATE_ALLOC_OWNER':'1'})]
    for label,extra in cases:
        cmd=['/usr/bin/leaks','--atExit','--',str(root/'builds/token_audit_release/ivf_gate'),str(root/'testdata/generated'/(stream+'.ivf')),'8','1']
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=60,env=dict(os.environ,MallocStackLogging='1',**extra))
        txt=p.stdout+p.stderr;(root/'logs'/f'leaks_{stream}_{label}.log').write_text(txt)
        matches=re.findall(r'(\d+) leaks for (\d+) total leaked bytes',txt)
        ok=bool(matches) and all(a=='0' and b=='0' for a,b in matches)
        results.append(dict(workload=stream,case=label,tool_exit=p.returncode,leak_reports=matches,pass_gate=ok))
        (root/'results/leak_checks.json').write_text(json.dumps(results,indent=2)+'\n')
        if not ok:raise RuntimeError(stream+' '+label+' failed or no report')
    print(stream,'12 leak checks PASS',flush=True)
