from pathlib import Path
import os,sys,json,hashlib,subprocess,time,math,csv
import numpy as np
root=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def decode(variant,workload,w,delay=0):
    cmd=[str(root/'builds'/f'{variant}_release'/'ivf_gate'),str(root/'testdata/generated'/(workload+'.ivf')),str(w),'1']
    env=dict(os.environ,CDEF_GATE_DELAY_NS=str(delay))
    start=time.time();p=subprocess.run(cmd,capture_output=True,text=True,timeout=120,env=env)
    if p.returncode:raise RuntimeError((cmd,p.returncode,p.stderr))
    return dict(json.loads(p.stdout),wall_timestamp=start,loadavg=list(os.getloadavg()))
mode=sys.argv[1]
if mode=='freeze':
    assert not (root/'protocol/protocol.json').exists(), 'Never silently refreeze'
    workloads=json.loads((root/'results/timing_workloads.json').read_text());pilots=json.loads((root/'results/pilot_workloads.json').read_text())
    calibration=[]
    for s in pilots+workloads:
        out=decode('token',s['id'],8);calibration.append(dict(workload=s['id'],output=out))
    perframe=max(x['output']['decode_ns']/x['output']['input_packets'] for x in calibration)
    dose=max(10_000_000,math.ceil(perframe*0.5/1_000_000)*1_000_000)
    assert all(dose*x['output']['input_packets']/x['output']['decode_ns']>0.08 for x in calibration)
    (root/'results/timing_calibration.json').write_text(json.dumps(calibration,indent=2)+'\n')
    lock=json.loads((root/'protocol/protocol_design.json').read_text())
    lock.update(confirmation_lock_unix=time.time(),delay_ns_per_packet=dose,workloads=[x['id'] for x in workloads],sensitivity_threads=8)
    paths=[root/'scripts/ivf_gate.c',root/'scripts/run_timing.py',root/'patches/baseline_to_type_fix.patch',root/'patches/type_fix_to_token.patch']
    paths += [root/'builds'/f'{v}_release'/'ivf_gate' for v in ['baseline','type_fix','token']]
    paths += [root/'testdata/generated'/(s['id']+'.ivf') for s in workloads]
    lock['sha256']={str(p.relative_to(root)):sha(p) for p in paths}
    p=root/'protocol/protocol.json';p.write_text(json.dumps(lock,indent=2)+'\n')
    (root/'protocol/protocol.sha256').write_text(sha(p)+'  protocol.json\n')
    print('FROZEN',sha(p),'dose_ns',dose,flush=True)
elif mode=='confirm':
    lock=json.loads((root/'protocol/protocol.json').read_text())
    for name,h in lock['sha256'].items():assert sha(root/name)==h,name
    assert not (root/'results/timing_results.json').exists(), 'Do not overwrite measurements'
    rows=[];cell=0
    jobs=[('primary',s,w) for s in lock['workloads'] for w in lock['timing']['threads']]
    jobs += [('sensitivity',s,8) for s in lock['workloads']]
    for kind,workload,w in jobs:
        for rep in range(-1,12):
            order=['A','B'] if (rep+cell)%2==0 else ['B','A'];obs={}
            for label in order:
                variant=('type_fix' if label=='A' else 'token') if kind=='primary' else 'token'
                delay=lock['delay_ns_per_packet'] if kind=='sensitivity' and label=='B' else 0
                obs[label]=decode(variant,workload,w,delay)
                time.sleep(0.15)
            assert obs['A']['pixel_sha256']==obs['B']['pixel_sha256']
            assert obs['A']['output_frames']==obs['B']['output_frames']==18
            rows.append(dict(kind=kind,workload=workload,threads=w,cell=cell,repetition=rep,order=''.join(order),A=obs['A'],B=obs['B'],ratio=obs['B']['decode_ns']/obs['A']['decode_ns']))
            (root/'results/timing_results.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(kind,workload,w,'complete',flush=True);cell+=1
    with (root/'results/timing_results.csv').open('w') as f:
        fields=['kind','workload','threads','cell','repetition','order','A_ns','B_ns','ratio','pixel_sha256'];writer=csv.DictWriter(f,fields);writer.writeheader()
        for r in rows:writer.writerow({**{k:r[k] for k in fields[:6]},'A_ns':r['A']['decode_ns'],'B_ns':r['B']['decode_ns'],'ratio':r['ratio'],'pixel_sha256':r['A']['pixel_sha256']})
elif mode=='analyze':
    lock=json.loads((root/'protocol/protocol.json').read_text());rows=json.loads((root/'results/timing_results.json').read_text());summary=[]
    for cell in sorted({r['cell'] for r in rows}):
        sample=[r for r in rows if r['cell']==cell and r['repetition']>=0];assert len(sample)==12
        rng=np.random.default_rng(192929+cell);a=np.array([r['ratio'] for r in sample]);boot=np.median(rng.choice(a,size=(50000,len(a)),replace=True),axis=1)
        lo,hi=np.quantile(boot,[.025,.975]);med=float(np.median(a));first=sample[0]
        s=dict(kind=first['kind'],workload=first['workload'],threads=first['threads'],median_ratio=med,ci95=[float(lo),float(hi)],min_ratio=float(a.min()))
        if s['kind']=='primary':s['status']='PASS' if hi<=1.02 else 'STOP_MATERIAL_SLOWDOWN' if lo>1.02 else 'NARROW_INCONCLUSIVE'
        else:
            dose=np.median([(r['B']['decode_ns']-r['A']['decode_ns'])/(r['A']['input_packets']*lock['delay_ns_per_packet']) for r in sample]);s['dose_accounting']=float(dose)
            s['status']='PASS' if med>1.08 and lo>1.05 and a.min()>1 and .5<=dose<=2 else 'FAIL_SENSITIVITY'
        summary.append(s)
    (root/'results/timing_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
else:raise ValueError(mode)
