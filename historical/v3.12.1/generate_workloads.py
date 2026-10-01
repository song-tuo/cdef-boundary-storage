from pathlib import Path
import numpy as np
import json, subprocess, hashlib, sys
root=Path(__file__).resolve().parents[1]
out=root/'testdata/generated';out.mkdir(exist_ok=True)
mode=sys.argv[1] if len(sys.argv)>1 else 'correctness'
specs=[]
if mode=='correctness':
    for depth in [8,10,12]:
        for chroma in ['420','422','444','mono']:
            specs.append(dict(id=f'odd_{depth}_{chroma}',width=321,height=259,frames=5,depth=depth,chroma=chroma,family='checker',seed=19291,tiles=1,parallel=depth%2))
    for h in [1,63,64,65,127,129]:
        specs.append(dict(id=f'edge_65x{h}',width=65,height=h,frames=3,depth=8,chroma='420',family='waves',seed=19292,tiles=0,parallel=0))
elif mode in ['timing','pilot']:
    for family,seed in [('waves',19293),('checker',19294),('texture',19295)]:
        for w,h in ([(1920,1080),(3840,2160)] if mode=='timing' else [(960,540)]):
            specs.append(dict(id=f'{mode}_{family}_{w}x{h}',width=w,height=h,frames=18 if mode=='timing' else 6,depth=8,chroma='420',family=family,seed=seed+(100 if mode=='pilot' else 0),tiles=1,parallel=1))
else: raise ValueError(mode)
(root/'protocol'/f'{mode}_workload_plan.json').write_text(json.dumps(specs,indent=2)+'\n')
results=[]
for spec in specs:
    raw=out/(spec['id']+'.yuv');ivf=out/(spec['id']+'.ivf')
    depth=spec['depth'];w=spec['width'];h=spec['height'];rng=np.random.default_rng(spec['seed'])
    chroma=spec['chroma']; ssx=0 if chroma=='444' else 1;ssy=1 if chroma in ['420','mono'] else 0
    with raw.open('wb') as f:
        for t in range(spec['frames']):
            for p in range(3):
                pw=(w+(1<<ssx)-1)>>ssx if p else w;ph=(h+(1<<ssy)-1)>>ssy if p else h
                y,x=np.ogrid[:ph,:pw]
                if spec['family']=='waves':
                    a=128+64*np.sin((x+t*9+p*13)/23)+40*np.cos((y-t*5)/31)+rng.integers(-4,5,(ph,pw))
                elif spec['family']=='checker':
                    a=45+150*((((x+t*7)//17)^((y+t*3)//23))&1)+25*np.sin((x+y)/17)+rng.integers(-8,9,(ph,pw))
                else:
                    coarse=rng.integers(20,230,((ph+15)//16,(pw+15)//16))
                    a=np.repeat(np.repeat(coarse,16,axis=0),16,axis=1)[:ph,:pw]+rng.integers(-16,17,(ph,pw))
                a=np.clip(a,16,235).astype(np.uint16)*(1<<(depth-8))
                f.write(a.astype('u1' if depth==8 else '<u2').tobytes())
    # aomenc 3.12.1 calls chroma controls before codec initialization when
    # non-420 12-bit input is explicitly profile 2. Its normal automatic
    # profile promotion avoids that application bug without changing libaom.
    profile=0 if depth==12 and chroma in ['422','444'] else 2 if depth==12 or chroma=='422' else 1 if chroma=='444' else 0
    cmd=[str(root/'builds/baseline_release/aomenc'),str(raw),'-o',str(ivf),'--ivf','--passes=1','--good','--cpu-used=6','--end-usage=q','--cq-level=44','--lag-in-frames=0','--threads=4','--row-mt=1','--enable-cdef=1','--kf-max-dist=9',f'--width={w}',f'--height={h}',f'--limit={spec["frames"]}',f'--bit-depth={depth}',f'--input-bit-depth={depth}',f'--profile={profile}',f'--i{"420" if chroma=="mono" else chroma}',f'--tile-columns={spec["tiles"]}',f'--frame-parallel={spec["parallel"]}']
    if depth==12:
        cmd += [f'--input-chroma-subsampling-x={ssx}', f'--input-chroma-subsampling-y={ssy}']
    if chroma=='mono':cmd+=['--monochrome']
    with (root/'logs'/(spec['id']+'.encode.log')).open('w') as log: ret=subprocess.run(cmd,stdout=log,stderr=log).returncode
    item=dict(spec,command=cmd,status=ret,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
    if not ret:item.update(ivf_sha256=hashlib.sha256(ivf.read_bytes()).hexdigest(),ivf_bytes=ivf.stat().st_size)
    results.append(item);(root/'results'/f'{mode}_workloads.json').write_text(json.dumps(results,indent=2)+'\n')
    raw.unlink() # Reproducible generated intermediate; hash and recipe retained.
    print(spec['id'],ret,flush=True)
    if ret:sys.exit(ret)
