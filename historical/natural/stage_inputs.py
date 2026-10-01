#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,time,subprocess,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parents[2]/'CDEF_full_source_gate'
P=json.loads((ROOT/'protocol/protocol.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def downscale(src,dst):
 assert not dst.exists()
 with src.open('rb') as fi,dst.open('xb') as fo:
  for _ in range(60):
   for w,h in [(3840,2160),(1920,1080),(1920,1080)]:
    b=fi.read(w*h);assert len(b)==w*h
    x=np.frombuffer(b,np.uint8).reshape(h,w).astype(np.uint16)
    y=(x[0::2,0::2]+x[0::2,1::2]+x[1::2,0::2]+x[1::2,1::2]+2)//4
    fo.write(y.astype(np.uint8).tobytes())
  assert not fi.read(1)
 assert dst.stat().st_size==1920*1080*3//2*60

def main():
 manifest=[]
 for name in P['selection']['sequences']:
  src=ROOT/'media'/f'{name}_3840x2160_first60.yuv'
  assert src.stat().st_size==3840*2160*3//2*60
  assert sha(src)==json.loads((ROOT/'sources'/f'{name}.json').read_text())['raw_sha256']
  small=ROOT/'media'/f'{name}_1920x1080_first60.yuv'
  if not small.exists():downscale(src,small)
  for w,h in P['matrix']['resolutions']:
   stem=f'{name}_{w}x{h}_first60';raw=ROOT/'media'/(stem+'.yuv');ivf=ROOT/'media'/(stem+'.ivf');meta=ROOT/'sources'/(stem+'.encode.json')
   if meta.exists():
    row=json.loads(meta.read_text());assert sha(ivf)==row['ivf_sha256'];manifest.append(row);continue
   assert not ivf.exists(),'Partial IVF exists; retain failure and inspect'
   cmd=[P['encoding']['binary'],str(raw),'-o',str(ivf)]+P['encoding']['flags']+[f'--width={w}',f'--height={h}']
   start=time.time()
   with (ROOT/'logs'/(stem+'.encode.log')).open('x') as f:ret=subprocess.run(cmd,stdout=f,stderr=f).returncode
   row={'id':stem,'name':name,'width':w,'height':h,'frames':60,'raw_sha256':sha(raw),'raw_bytes':raw.stat().st_size,'command':cmd,'exit_code':ret,'start_unix':start,'duration_seconds':time.time()-start}
   if ret==0:row.update(ivf_sha256=sha(ivf),ivf_bytes=ivf.stat().st_size)
   meta.write_text(json.dumps(row,indent=2)+'\n');assert ret==0,row
   manifest.append(row);print('ENCODED',stem,row['duration_seconds'],flush=True)
 locks=[ROOT/'protocol/protocol.json']+list((ROOT/'scripts').glob('*.py'))+[Path(P['encoding']['binary'])]
 for name in P['original_binaries_sha256']:locks.append(Path(P['encoding']['binary']).parent.parent/name/'ivf_gate')
 locks += [ROOT/'media'/(x['id']+'.ivf') for x in manifest]
 out=ROOT/'protocol/inputs.json';assert not out.exists()
 data={'frozen_at_unix':time.time(),'no_decoder_outcomes_observed':True,'protocol_sha256':sha(ROOT/'protocol/protocol.json'),'streams':manifest,'files':{str(p):sha(p) for p in locks},'numpy_version':np.__version__}
 out.write_text(json.dumps(data,indent=2)+'\n');(ROOT/'protocol/inputs.sha256').write_text(sha(out)+'  inputs.json\n');print('INPUTS_FROZEN',sha(out),flush=True)
if __name__=='__main__':main()
