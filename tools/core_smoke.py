#!/usr/bin/env python3
from pathlib import Path
import argparse,json,subprocess,os
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--input',type=Path);p.add_argument('--width',type=int,default=3840);p.add_argument('--height',type=int,default=2160);p.add_argument('--frames',type=int,default=2);p.add_argument('--run-name',default='core_smoke');a=p.parse_args();assert Path(a.run_name).name==a.run_name;w=a.work.resolve();ivf=a.input.resolve() if a.input else w/'testdata/generated/smoke_waves_3840x2160.ivf';dest=w/'runs'/a.run_name;dest.mkdir(parents=True,exist_ok=False)
rows=[];env={k:v for k,v in os.environ.items() if not k.startswith('CDEF_GATE_')};env['CDEF_GATE_DELAY_NS']='0'
for workers in [8,16]:
 for v in ['baseline','type_fix','token','baseline_audit','type_fix_audit','token_audit']:
  rid=f'{v}_w{workers}';cmd=[str(w/'builds'/(v+'_release')/'ivf_gate'),str(ivf),str(workers),'1'];q=subprocess.run(cmd,capture_output=True,text=True,timeout=120,env=env)
  (dest/(rid+'.stdout')).write_text(q.stdout);(dest/(rid+'.stderr')).write_text(q.stderr);assert q.returncode==0,rid
  o=json.loads(q.stdout);assert o['output_frames']==a.frames and o['status']==o['destroy_status']==0
  row={'variant':v,'workers':workers,'output':o}
  if v.endswith('_audit'):
   events=[json.loads(l) for l in q.stderr.splitlines() if l.startswith('{')];events=[e for e in events if e['event']=='cdef_frame'];assert events,'CDEF inactive; this smoke does not validate allocation'
   R=(a.height+63)//64;stride=((a.width+3)//4*4+15)//16*16;L=4*(stride+2*(stride//2));K=min(2*R-2,2*workers+1);expected=2*R*L*(4 if v.startswith('baseline') else 1) if not v.startswith('token') else K*L
   assert all(e['workers']==workers and e['requested_bytes']==expected for e in events),rid;row.update(cdef_active_frames=len(events),requested_bytes=expected)
  rows.append(row)
 assert len({r['output']['pixel_sha256'] for r in rows if r['workers']==workers})==1
(dest/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS',len(rows),'fresh processes; correctness and allocation only, no timing inference')
