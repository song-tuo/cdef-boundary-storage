from pathlib import Path
import json,hashlib,subprocess,os,time,random,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];NAT=ROOT.parent/'CDEF_paper_pipeline/revision_20260930/natural'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def cells():return [dict(cell=i,scene=s,workers=w,stream=s+'_3840x2160_first60') for i,(s,w) in enumerate((s,w) for s in ['Beauty','Jockey','HoneyBee'] for w in [8,16])]
def freeze():
 assert (ROOT/'results/GATES_PASS.json').exists()
 p=ROOT/'protocol/FREEZE.json';assert not p.exists()
 rng=random.Random(2026100207);jobs=[]
 for block in range(-1,12):
  cc=cells();rng.shuffle(cc)
  for c in cc:
   orders=['AB','BA'];rng.shuffle(orders)
   for pair,ab in enumerate(orders):jobs.append(dict(block=block,pair=pair,order=ab,**c))
 schedule=ROOT/'protocol/schedule.json';schedule.write_text(json.dumps(jobs,indent=2)+'\n')
 paths=[ROOT/'protocol/SUPPLEMENTARY_PROTOCOL.md',schedule,Path(__file__).resolve(),ROOT/'scripts/ivf_gate.c',ROOT/'results/GATES_PASS.json']
 paths += [p for v in ['ring','token'] for p in (ROOT/'src'/v).rglob('*') if p.is_file()]
 paths += [ROOT/'builds'/v/f for v in ['ring_release','token_release'] for f in ['ivf_gate','libaom.a','CMakeCache.txt','compile_commands.json']]
 paths += [NAT/'media'/f'{s}_3840x2160_first60.ivf' for s in ['Beauty','Jockey','HoneyBee']]
 data={'created_unix':time.time(),'endpoint':'cumulative_decode_call_ns','ratio':'ring/token','numpy_version':np.__version__,'files':{str(p):sha(p) for p in paths},'schedule_pairs':len(jobs)}
 p.write_text(json.dumps(data,indent=2)+'\n');(ROOT/'protocol/FREEZE.sha256').write_text(sha(p)+'  FREEZE.json\n');print('FROZEN',len(jobs),'pairs',sha(p),flush=True)
def verify():
 p=ROOT/'protocol/FREEZE.json';lock=json.loads(p.read_text());assert sha(p)==(ROOT/'protocol/FREEZE.sha256').read_text().split()[0]
 for path,h in lock['files'].items():assert sha(Path(path))==h,path
 return lock

def timing():
 verify();out=ROOT/'results/timing_pairs.jsonl';assert not out.exists();assert (ROOT/'protocol/QUIET_HOST_GO.json').exists()
 schedule=json.loads((ROOT/'protocol/schedule.json').read_text());env={k:v for k,v in os.environ.items() if not k.startswith(('CDEF_','ASAN_OPTIONS','TSAN_OPTIONS','UBSAN_OPTIONS'))}
 raw=[json.loads(l) for l in (NAT/'results/correctness_allocation.jsonl').read_text().splitlines()];expected={(r['stream'],r['workers']):r['output']['pixel_sha256'] for r in raw}
 for job in schedule:
  obs={}
  for label in job['order']:
   variant='token_release' if label=='A' else 'ring_release';rid=f'timing_b{job["block"]:02d}_c{job["cell"]}_p{job["pair"]}_{label}';prefix=ROOT/'logs'/rid
   assert not prefix.with_suffix('.json').exists()
   cmd=[str(ROOT/'builds'/variant/'ivf_gate'),str(NAT/'media'/(job['stream']+'.ivf')),str(job['workers']),'1'];start=time.time()
   try:r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120);stdout=r.stdout;stderr=r.stderr;rc=r.returncode
   except subprocess.TimeoutExpired as e:stdout=e.stdout or b'';stderr=e.stderr or b'';rc='TIMEOUT'
   if isinstance(stdout,bytes):stdout=stdout.decode(errors='replace')
   if isinstance(stderr,bytes):stderr=stderr.decode(errors='replace')
   prefix.with_suffix('.stdout').write_text(stdout);prefix.with_suffix('.stderr').write_text(stderr)
   rec={'id':rid,'variant':variant,'command':cmd,'start_unix':start,'end_unix':time.time(),'exit_code':rc,'load_average':os.getloadavg()}
   try:rec['output']=json.loads(stdout)
   except Exception:pass
   prefix.with_suffix('.json').write_text(json.dumps(rec,indent=2)+'\n')
   assert rc==0 and rec['output']['status']==rec['output']['destroy_status']==0,rec
   assert rec['output']['pixel_sha256']==expected[(job['stream'],job['workers'])] and rec['output']['output_frames']==60,rec
   obs[label]=rec;time.sleep(.20)
  row={**job,**obs,'ratio':obs['B']['output']['decode_ns']/obs['A']['output']['decode_ns']}
  with out.open('a') as f:f.write(json.dumps(row)+'\n')
  if job['pair']==1:print('BLOCK_CELL_DONE',job['block'],job['cell'],flush=True)
 verify();print('TIMING_COMPLETE',flush=True)
def analyze():
 verify();rows=[json.loads(x) for x in (ROOT/'results/timing_pairs.jsonl').read_text().splitlines()];assert len(rows)==156
 summary=[]
 for c in cells():
  rr=[r for r in rows if r['cell']==c['cell'] and r['block']>=0];assert len(rr)==24
  a=np.array([[next(r['ratio'] for r in rr if r['block']==b and r['pair']==p) for p in range(2)] for b in range(12)])
  rng=np.random.default_rng(2026100208+c['cell']);idx=rng.integers(0,12,size=(50000,12));boot=np.median(a[idx].reshape(50000,24),axis=1);lo,hi=np.quantile(boot,[.025,.975],method='linear')
  summary.append({**c,'pairs':24,'median_ratio':float(np.median(a)),'ci95':[float(lo),float(hi)],'token_median_ms':float(np.median([r['A']['output']['decode_ns']/1e6 for r in rr])),'ring_median_ms':float(np.median([r['B']['output']['decode_ns']/1e6 for r in rr]))})
 (ROOT/'results/timing_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':{'freeze':freeze,'timing':timing,'analyze':analyze}[sys.argv[1]]()
