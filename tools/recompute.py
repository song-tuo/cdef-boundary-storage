#!/usr/bin/env python3
"""Recompute both paper tables and all historical timing screens from exported raw values."""
from pathlib import Path
import argparse,json,csv,hashlib,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def jl(p):return [json.loads(x) for x in p.read_text().splitlines()]
def save(out,name,rows):
 (out/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
 if rows:
  with (out/(name+'.csv')).open('w',newline='') as f:w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'computed');args=parser.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
 lineage=load(ROOT/'provenance/export_lineage.json');assert all(hashlib.sha256((ROOT/x['export_path']).read_bytes()).hexdigest()==x['export_sha256'] for x in lineage['files'])
 n=ROOT/'evidence/natural';pairs=jl(n/'results/timing_pairs.jsonl');audit=jl(n/'results/correctness_allocation.jsonl');expected=load(n/'results/timing_summary.json');schedule=load(n/'protocol/executed_schedule.json');assert len(pairs)==312 and len(audit)==72
 for a,b in zip(pairs,schedule):assert all(a[k]==b[k] for k in ['cell','block','pair','workers','order'])
 natural=[]
 for cell in range(12):
  rows=[r for r in pairs if r['cell']==cell];assert len(rows)==26
  h={r['output']['pixel_sha256'] for r in audit if r['cell']==cell};assert len(h)==1
  for r in rows:
   for label in ['A','B']:
    o=r[label]['output'];assert o['pixel_sha256'] in h and o['output_frames']==60 and r[label]['exit_code']==0
    rid=r[label]['id'];assert load(n/'logs'/(rid+'.stdout'))==o
    assert load(n/'logs'/(rid+'.json'))['output']==o
   assert r['ratio']==r['B']['output']['decode_ns']/r['A']['output']['decode_ns']
  for block in range(-1,12):assert sorted(r['order'] for r in rows if r['block']==block)==['AB','BA']
  a=np.array([[next(r['ratio'] for r in rows if r['block']==b and r['pair']==p) for p in range(2)] for b in range(12)])
  rng=np.random.default_rng(2026093002+cell);idx=rng.integers(0,12,size=(50000,12));boot=np.median(a[idx].reshape(50000,24),axis=1);lo,hi=np.quantile(boot,[.025,.975],method='linear');median=float(np.median(a));exp=expected[cell]
  assert np.allclose([median,lo,hi],[exp['median_ratio'],*exp['ci95']],atol=1e-14,rtol=0)
  natural.append({'stream':rows[0]['stream'],'workers':rows[0]['workers'],'median_ratio':median,'ci95_lower':float(lo),'ci95_upper':float(hi),'status':'PASS_NONINFERIOR_SCREEN' if hi<=1.02 else 'MATERIAL_SLOWDOWN' if lo>1.02 else 'INCONCLUSIVE'})
 save(out,'table_2_natural_timing',natural)
 for r in audit:
  assert load(n/'logs'/(r['id']+'.stdout'))==r['output']
  if 'activity' in r:
   events=[json.loads(l) for l in (n/'logs'/(r['id']+'.stderr')).read_text().splitlines() if l.startswith('{')];c=[e for e in events if e['event']=='cdef_frame'];assert len(c)==r['activity']['events']==60
   assert max(e['requested_bytes'] for e in c)==r['activity']['requested_bytes']==r['expected_requested_bytes']
 memory=load(ROOT/'evidence/synthetic/results/memory_results.json');assert len(memory)==90
 table=[]
 for width,height in [(1920,1080),(3840,2160),(7680,4320)]:
  R=(height+63)//64;stride=((width+3)//4*4+15)//16*16;L=4*(stride+2*(stride//2))
  for W in [8,16]:
   K=min(2*R-2,2*W+1);fix=2*R*L;token=K*L
   if width<7680:
    for variant,expected_bytes in [('type_fix',fix),('token',token)]:
     values=[r['requested_bytes'] for r in memory if r['width']==width and r['requested_threads']==W and r['variant']==variant];assert len(values)==3 and set(values)=={expected_bytes}
     vals=[r['activity']['requested_bytes'] for r in audit if ('1920' if width==1920 else '3840') in r['stream'] and r['workers']==W and r['build']==variant+'_audit_release'];assert len(vals)==3 and set(vals)=={expected_bytes}
   table.append({'width':width,'height':height,'R':R,'W':W,'kind':'analytical_projection' if width==7680 else 'measured','type_fix_KiB':fix/1024,'token_KiB':token/1024,'reduction_percent':100*(1-token/fix)})
 save(out,'table_1_boundary_capacity',table)
 old=load(ROOT/'evidence/synthetic/results/timing_results.json');protocol=load(ROOT/'evidence/synthetic/protocol/protocol.json');exps=load(ROOT/'evidence/synthetic/results/timing_summary.json');assert len(old)==312;synthetic=[];posthoc=[]
 for r in old:
  assert r['A']['pixel_sha256']==r['B']['pixel_sha256'] and r['A']['output_frames']==r['B']['output_frames']==18
  assert r['ratio']==r['B']['decode_ns']/r['A']['decode_ns']
 for cell in sorted({r['cell'] for r in old}):
  rows=[r for r in old if r['cell']==cell and r['repetition']>=0];assert len(rows)==12
  a=np.array([r['ratio'] for r in rows]);rng=np.random.default_rng(192929+cell);b=np.median(rng.choice(a,size=(50000,12),replace=True),axis=1);lo,hi=np.quantile(b,[.025,.975],method='linear');med=float(np.median(a));e=exps[cell]
  assert np.allclose([med,lo,hi],[e['median_ratio'],*e['ci95']],atol=1e-14,rtol=0)
  kind=rows[0]['kind'];dose=None
  if kind=='primary':status='PASS' if hi<=1.02 else 'STOP_MATERIAL_SLOWDOWN' if lo>1.02 else 'NARROW_INCONCLUSIVE'
  else:
   dose=float(np.median([(r['B']['decode_ns']-r['A']['decode_ns'])/(r['A']['input_packets']*protocol['delay_ns_per_packet']) for r in rows]));assert abs(dose-e['dose_accounting'])<1e-14
   status='PASS' if med>1.08 and lo>1.05 and a.min()>1 and .5<=dose<=2 else 'FAIL_SENSITIVITY'
  assert status==e['status']
  synthetic.append({'kind':rows[0]['kind'],'workload':rows[0]['workload'],'threads':rows[0]['threads'],'median_ratio':med,'ci95_lower':float(lo),'ci95_upper':float(hi),'frozen_status':status,'dose_accounting':dose})
  if rows[0]['kind']=='primary':
   rng=np.random.default_rng(8192929+cell);idx=rng.integers(0,6,size=(50000,6));bb=np.median(a.reshape(6,2)[idx].reshape(50000,12),axis=1);l,h=np.quantile(bb,[.025,.975],method='linear');posthoc.append({'workload':rows[0]['workload'],'threads':rows[0]['threads'],'ci95_lower':float(l),'ci95_upper':float(h),'status':'POST_HOC_DIAGNOSTIC_NOT_ORIGINAL_SCREEN'})
 save(out,'synthetic_frozen_timing',synthetic);save(out,'synthetic_posthoc_block_diagnostic',posthoc)
 checks={'export_files_verified':len(lineage['files']),'natural_process_records_verified':624,'natural_audit_records_verified':72,'natural_pairs_including_warmup':312,'synthetic_pairs_including_controls_warmup':312,'memory_rows':90,'natural_primary_bootstrap_matches':12,'synthetic_primary_and_control_bootstrap_matches':24,'table_1_rows':6,'table_2_rows':12,'numpy_version':np.__version__,'new_performance_measurements':False}
 (out/'checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
