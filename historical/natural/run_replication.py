#!/usr/bin/env python3
from pathlib import Path
import sys,json,subprocess,os,time,hashlib,random,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'protocol/protocol.json').read_text())
I=json.loads((ROOT/'protocol/inputs.json').read_text())
OLD=Path(P['encoding']['binary']).parents[2]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 for f,h in I['files'].items():assert sha(Path(f))==h,f
 assert sha(ROOT/'protocol/protocol.json')==I['protocol_sha256']
def cells():return [{'cell':i,'stream':s,'workers':w} for i,(s,w) in enumerate((s,w) for s in I['streams'] for w in P['matrix']['workers'])]
def run(build,s,w,rid):
 path=ROOT/'logs'/rid;assert not path.with_suffix('.json').exists(),rid
 cmd=[str(OLD/'builds'/build/'ivf_gate'),str(ROOT/'media'/(s['id']+'.ivf')),str(w),'1']
 start=time.time();env={k:v for k,v in os.environ.items() if not k.startswith('CDEF_GATE_')};env['CDEF_GATE_DELAY_NS']='0'
 try:
  q=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120)
  status=q.returncode;stdout=q.stdout;stderr=q.stderr
 except subprocess.TimeoutExpired as e:status='TIMEOUT';stdout=e.stdout or '';stderr=e.stderr or ''
 if isinstance(stdout,bytes):stdout=stdout.decode(errors='replace')
 if isinstance(stderr,bytes):stderr=stderr.decode(errors='replace')
 path.with_suffix('.stdout').write_text(stdout);path.with_suffix('.stderr').write_text(stderr)
 record={'id':rid,'command':cmd,'start_unix':start,'end_unix':time.time(),'exit_code':status,'load_average':list(os.getloadavg())}
 try:record['output']=json.loads(stdout)
 except Exception:pass
 path.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n')
 assert status==0,record
 out=record['output'];assert out['status']==out['destroy_status']==0 and out['output_frames']==60 and out['input_packets']==60 and out['truncated_input']==0,record
 return record

def audit():
 dest=ROOT/'results/correctness_allocation.jsonl';assert not dest.exists()
 for c in cells():
  s=c['stream'];w=c['workers'];hashes=[]
  for build in P['correctness']['builds']+P['activity_allocation']['builds']:
   rid=f'cell{c["cell"]:02d}_{s["id"]}_w{w}_{build}'
   r=run(build,s,w,rid);r.update(cell=c['cell'],stream=s['id'],workers=w,build=build);hashes.append(r['output']['pixel_sha256'])
   if '_audit_' in build:
    events=[json.loads(l) for l in (ROOT/'logs'/(rid+'.stderr')).read_text().splitlines() if l.startswith('{')]
    active=[e for e in events if e['event']=='cdef_frame'];assert active,'Zero-active failure; preserve, do not replace'
    r['activity']={'events':len(active),'output_frames':60,'max_workers':max(e['workers'] for e in active),'rows':max(e['rows'] for e in active),'requested_bytes':max(e['requested_bytes'] for e in active),'usable_bytes':max(e['usable_bytes'] for e in active)}
    R=(s['height']+63)//64;L=4*(s['width']+2*((s['width']+1)//2));K=min(2*R-2,2*w+1)
    expected=(2*R*L*4 if build.startswith('baseline') else 2*R*L if build.startswith('type_fix') else K*L)
    r['expected_requested_bytes']=expected
    assert r['activity']['max_workers']==w and r['activity']['rows']==R and r['activity']['requested_bytes']==expected,r
   with dest.open('a') as f:f.write(json.dumps(r)+'\n')
  assert len(set(hashes))==1,(c,hashes)
  print('CORRECTNESS_ALLOCATION_PASS',c['cell'],s['id'],w,flush=True)

def timing():
 go=ROOT/'protocol/TIMING_GO.json';assert go.exists(),'Parent GO required'
 result=ROOT/'results/timing_pairs.jsonl';assert not result.exists(),'No silent overwrite/resume'
 subprocess.run(['ps','-axo','pid,ppid,%cpu,comm'],stdout=(ROOT/'logs/timing_process_snapshot.txt').open('w'))
 rng=random.Random(P['timing']['random_seed']);schedule=[]
 for block in range(-1,P['timing']['blocks']):
  order=cells();rng.shuffle(order)
  for c in order:
   orders=['AB','BA'];rng.shuffle(orders)
   for pair,ab in enumerate(orders):schedule.append({'block':block,'pair':pair,'order':ab,**c})
 (ROOT/'protocol/executed_schedule.json').write_text(json.dumps(schedule,indent=2)+'\n')
 for job in schedule:
  obs={};c=job['cell'];s=job['stream'];w=job['workers']
  for label in job['order']:
   build='type_fix_release' if label=='A' else 'token_release'
   rid=f'timing_b{job["block"]:02d}_c{c:02d}_p{job["pair"]}_{label}'
   obs[label]=run(build,s,w,rid);time.sleep(P['timing']['inter_process_cooldown_seconds'])
  assert obs['A']['output']['pixel_sha256']==obs['B']['output']['pixel_sha256']
  row={k:job[k] for k in ['block','pair','order','cell','workers']};row.update(stream=s['id'],A=obs['A'],B=obs['B'],ratio=obs['B']['output']['decode_ns']/obs['A']['output']['decode_ns'])
  with result.open('a') as f:f.write(json.dumps(row)+'\n')
  if job['pair']==1:print('TIMING_BLOCK_CELL_DONE',job['block'],c,flush=True)
 print('TIMING_COMPLETE',flush=True)

def analyze():
 rows=[json.loads(l) for l in (ROOT/'results/timing_pairs.jsonl').read_text().splitlines()]
 assert len(rows)==12*26,len(rows)
 summary=[]
 for c in cells():
  z=[r for r in rows if r['cell']==c['cell'] and r['block']>=0];assert len(z)==24
  a=np.array([[next(r['ratio'] for r in z if r['block']==b and r['pair']==p) for p in range(2)] for b in range(12)])
  rng=np.random.default_rng(2026093002+c['cell']);idx=rng.integers(0,12,size=(50000,12));boot=np.median(a[idx].reshape(50000,24),axis=1)
  lo,hi=np.quantile(boot,[.025,.975],method='linear')
  summary.append({'cell':c['cell'],'stream':c['stream']['id'],'workers':c['workers'],'n_pairs':24,'n_blocks':12,'median_ratio':float(np.median(a)),'ci95':[float(lo),float(hi)],'type_fix_median_ms':float(np.median([r['A']['output']['decode_ns']/1e6 for r in z])),'token_median_ms':float(np.median([r['B']['output']['decode_ns']/1e6 for r in z])),'min_ratio':float(a.min()),'max_ratio':float(a.max()),'status':'PASS_NONINFERIOR_SCREEN' if hi<=1.02 else 'MATERIAL_SLOWDOWN' if lo>1.02 else 'INCONCLUSIVE'})
 (ROOT/'results/timing_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 with (ROOT/'results/timing_summary.csv').open('w') as f:
  w=csv.DictWriter(f,summary[0].keys());w.writeheader();w.writerows(summary)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 verify();{'audit':audit,'timing':timing,'analyze':analyze}[sys.argv[1]]()
