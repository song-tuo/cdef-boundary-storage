#!/usr/bin/env python3
"""Generate six natural inputs in a NEW work area; historical evidence is never overwritten."""
from pathlib import Path
import sys,json,hashlib,subprocess,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];WORK=Path(sys.argv[1]).resolve();N=WORK/'natural';P=json.loads((ROOT/'evidence/natural/protocol/protocol.json').read_text());expected=json.loads((ROOT/'evidence/natural/protocol/inputs.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
manifest=[]
for name in P['selection']['sequences']:
 source=N/'media'/f'{name}_3840x2160_first60.yuv';source_spec=json.loads((ROOT/'evidence/natural/sources'/f'{name}.json').read_text());assert source.stat().st_size==source_spec['raw_bytes'] and sha(source)==source_spec['raw_sha256']
 small=N/'media'/f'{name}_1920x1080_first60.yuv'
 if not small.exists():
  with source.open('rb') as f,small.open('xb') as o:
   for frame in range(60):
    for width,height in [(3840,2160),(1920,1080),(1920,1080)]:
     x=np.frombuffer(f.read(width*height),np.uint8).reshape(height,width).astype(np.uint16);o.write(((x[::2,::2]+x[::2,1::2]+x[1::2,::2]+x[1::2,1::2]+2)//4).astype(np.uint8).tobytes())
 for width,height in P['matrix']['resolutions']:
  stem=f'{name}_{width}x{height}_first60';raw=N/'media'/(stem+'.yuv');ivf=N/'media'/(stem+'.ivf');assert not ivf.exists(),'Use new work area, do not replace outcomes'
  cmd=[str(WORK/'builds/baseline_release/aomenc'),str(raw),'-o',str(ivf),*P['encoding']['flags'],f'--width={width}',f'--height={height}'];t=time.time()
  with (N/'logs'/(stem+'.encode.log')).open('x') as f:subprocess.run(cmd,stdout=f,stderr=f,check=True)
  original=next(x for x in expected['streams'] if x['id']==stem);h=sha(ivf)
  manifest.append({'id':stem,'name':name,'width':width,'height':height,'frames':60,'command':cmd,'raw_sha256':sha(raw),'ivf_sha256':h,'matches_historical_bitstream':h==original['ivf_sha256'],'seconds':time.time()-t})
(N/'generated_inputs.json').write_text(json.dumps({'kind':'NEW_PORTABLE_REPRODUCTION_INPUTS_NOT_ORIGINAL_FROZEN_ARTIFACT','streams':manifest},indent=2)+'\n')
print('Generated',len(manifest),'streams; historical bitstream matches',sum(x['matches_historical_bitstream'] for x in manifest))
