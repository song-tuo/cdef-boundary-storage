from common import *
import numpy as np,concurrent.futures,struct,shutil
out=ROOT/'inputs';encoder=ROOT/'builds/type_fix_release/aomenc'
specs=json.loads((ROOT/'protocol/semantic_inputs.json').read_text());rawdir=ROOT/'inputs/raw_intermediates';rawdir.mkdir(exist_ok=True)
def encode(s):
 ident=s['id'];w=s['width'];h=s['height'];depth=s['depth'];chroma=s['chroma'];ss=1 if chroma=='420' else 0
 raw=rawdir/(ident+'.yuv');ivf=out/(ident+'.ivf');rng=np.random.default_rng(s['seed'])
 with raw.open('wb') as f:
  for t in range(s['frames']):
   for p in range(3):
    pw=(w+1)//2 if p and ss else w;ph=(h+1)//2 if p and ss else h;y,x=np.ogrid[:ph,:pw]
    a=45+150*((((x+t*7)//17)^((y+t*3)//23))&1)+25*np.sin((x+y)/17)+rng.integers(-8,9,(ph,pw));a=np.clip(a,16,235).astype(np.uint16)*(1<<(depth-8));f.write(a.astype('u1' if depth==8 else '<u2').tobytes())
 rawhash=sha(raw);profile=0 if depth==12 else 1 if chroma=='444' else 0
 cmd=[encoder,raw,'-o',ivf,'--ivf','--passes=1','--good','--cpu-used=8','--end-usage=q','--cq-level=44','--lag-in-frames=0','--threads=2','--row-mt=1',f'--enable-cdef={s["cdef_enabled"]}','--kf-max-dist=3',f'--width={w}',f'--height={h}',f'--limit={s["frames"]}',f'--bit-depth={depth}',f'--input-bit-depth={depth}',f'--profile={profile}',f'--i{chroma}','--tile-columns=1','--frame-parallel=0']
 if depth==12:cmd += [f'--input-chroma-subsampling-x={ss}',f'--input-chroma-subsampling-y={ss}']
 r=run('encode_'+ident,cmd,timeout=300);rec=s|{'raw_sha256':rawhash,'encode_exit':r['exit_code']}
 if not r['exit_code']:rec|={'sha256':sha(ivf),'bytes':ivf.stat().st_size};raw.unlink()
 save(ROOT/'results/input_records'/(ident+'.json'),rec);return rec
# Allocation inputs are frozen before generation and are additional to semantic grid.
alloc=[]
for w,h in [[1920,1080],[2560,1440],[3840,2160]]:
 alloc.append({'id':f'alloc_{w}x{h}','width':w,'height':h,'depth':8,'chroma':'420','cdef_enabled':1,'frames':3,'seed':310108,'family':'checker'})
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:records=list(ex.map(encode,specs+alloc))
save(ROOT/'inputs/generated_manifest.json',records)
assert all(x['encode_exit']==0 for x in records)
# A single IVF container keeps one decoder instance while sequence headers change dimensions.
seq=[]
for depth in [8,10,12]:
 for ch in ['420','444']:
  parts=[]
  for R,enable in [(3,1),(67,1),(3,1),(131,1),(1,1),(17,0),(17,1)]:
   s=next(x for x in specs if x['R']==R and x['depth']==depth and x['chroma']==ch and x['cdef_enabled']==enable);parts.append(s['id'])
  data=[(out/(i+'.ivf')).read_bytes() for i in parts];hdr=bytearray(data[0][:32]);hdr[24:28]=struct.pack('<I',21);name=f'sequence_{depth}_{ch}';path=out/(name+'.ivf');path.write_bytes(hdr+b''.join(d[32:] for d in data));seq.append({'id':name,'depth':depth,'chroma':ch,'frames':21,'parts':parts,'sha256':sha(path),'bytes':path.stat().st_size})
save(ROOT/'inputs/sequence_manifest.json',seq)
real=[]
for src in json.loads((ROOT/'protocol/real_content_inputs.json').read_text()):
 source=Path(src['source_path']);assert sha(source)==src['sha256'];ident=source.name.removesuffix('.y4m');local=out/source.name;shutil.copyfile(source,local)
 for q in [0,24,56]:
  dst=out/(f'real_{ident}_q{q}.ivf');cmd=[encoder,local,'-o',dst,'--ivf','--passes=1','--good','--cpu-used=6','--end-usage=q',f'--cq-level={q}','--lag-in-frames=0','--threads=2','--row-mt=1','--enable-cdef=1','--kf-max-dist=10','--limit=10','--tile-columns=0','--frame-parallel=0']
  if q==0:cmd+=['--lossless=1']
  r=run('encode_'+dst.stem,cmd,timeout=300);rec={'id':dst.stem,'content_id':source.name,'input_sha256':src['sha256'],'cq':q,'encode_exit':r['exit_code']}
  if not r['exit_code']:rec|={'sha256':sha(dst),'bytes':dst.stat().st_size}
  real.append(rec)
save(ROOT/'inputs/real_encoded_manifest.json',real);assert all(not x['encode_exit'] for x in real)
print('INPUTS COMPLETE',len(records),len(seq),len(real),flush=True)
