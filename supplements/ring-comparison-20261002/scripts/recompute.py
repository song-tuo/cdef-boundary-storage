"""Portable offline check of retained ring/token timing and diagnostic data."""
from pathlib import Path
import json, argparse
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=p.parse_args();root=args.root
rows=[json.loads(x) for x in (root/'results/timing_pairs.jsonl').read_text().splitlines()]
assert len(rows)==156 and len({(x['block'],x['cell'],x['pair']) for x in rows})==156
schedule=json.loads((root/'protocol/schedule.json').read_text())
for r,s in zip(rows,schedule):
 assert all(r[k]==v for k,v in s.items())
 for key in ['A','B']:
  o=r[key]['output'];assert r[key]['exit_code']==o['status']==o['destroy_status']==0 and o['output_frames']==60
 assert r['A']['output']['pixel_sha256']==r['B']['output']['pixel_sha256']
 assert r['ratio']==r['B']['output']['decode_ns']/r['A']['output']['decode_ns']
summary=[]
for cell in range(6):
 rr=[r for r in rows if r['cell']==cell and r['block']>=0];assert len(rr)==24
 a=np.array([[next(r['ratio'] for r in rr if r['block']==b and r['pair']==q) for q in range(2)] for b in range(12)])
 for b in range(12):assert sorted(r['order'] for r in rr if r['block']==b)==['AB','BA']
 rng=np.random.default_rng(2026100208+cell);idx=rng.integers(0,12,size=(50000,12));boot=np.median(a[idx].reshape(50000,24),axis=1)
 lo,hi=np.quantile(boot,[.025,.975],method='linear')
 summary.append(dict(cell=cell,median_ratio=float(np.median(a)),ci95=[float(lo),float(hi)]))
saved=json.loads((root/'results/timing_summary.json').read_text())
for a,b in zip(summary,saved):assert all(a[k]==b[k] for k in a)
gates=[json.loads(x) for x in (root/'results/gates.jsonl').read_text().splitlines()];assert len(gates)==486 and all(x['pass'] for x in gates)
diag=[dict(id=x['id'],**x['activity']) for x in gates if x['build']=='ring_diag' and x['id'].startswith('natural_')];assert len(diag)==6
for x in diag: assert x['frames']==60 and x['dispatch_rows']==2040
print(json.dumps(dict(status='PASS',timing=summary,diagnostic=diag),indent=2))
