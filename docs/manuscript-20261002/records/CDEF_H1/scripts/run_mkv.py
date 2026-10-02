from checks import *
import shutil,re,concurrent.futures
DATA=Path('${WORKSPACE}/CDEF_full_source_gate/testdata');manifest=[]
for d in ['sizeup','sizedown']:
 src=DATA/'generated'/f'conformance_{d}.ivf';dst=ROOT/'inputs'/src.name;shutil.copyfile(src,dst)
 official=DATA/f'av1-1-b8-03-{d}.mkv';md5=DATA/(official.name+'.md5');shutil.copyfile(md5,ROOT/'inputs'/md5.name)
 manifest.append({'direction':d,'official_source':str(official),'official_sha256':sha(official),'derived_payload_ivf':str(dst.relative_to(ROOT)),'ivf_sha256':sha(dst),'official_expected_frame_md5_sha256':sha(md5),'derivation':'read-only prior demux of unchanged official MKV payload; independently compare every new decode to official frame MD5'})
save(ROOT/'inputs/mkv_manifest.json',manifest)
def job(t):
 d,p,w,mt=t;tag=f'mkv_{d}_{p}_w{w}_m{mt}';cmd=[ROOT/'builds'/f'hybrid_{p}'/'aomdec','--md5','--rawvideo','--output=frame-%4.raw',f'--threads={w}',f'--row-mt={mt}',ROOT/'inputs'/f'conformance_{d}.ivf'];r=run(tag,cmd,env=SANENV,timeout=180)
 actual=[l.split()[0] for l in (ROOT/'logs'/(tag+'.stdout')).read_text().splitlines() if re.match(r'^[0-9a-f]{32} ',l)];expected=[l.split()[0] for l in (ROOT/'inputs'/f'av1-1-b8-03-{d}.mkv.md5').read_text().splitlines() if l.strip()]
 return {'category':'official_MKV_payload_conformance','input':d,'profile':p,'W':w,'row_mt':mt,'exit_code':r['exit_code'],'frames':len(actual),'expected_frames':len(expected),'frame_md5_match':actual==expected,'status':'PASS' if r['exit_code']==0 and actual==expected else 'FAIL','command_log':tag}
tasks=[(d,p,w,mt) for d in ['sizeup','sizedown'] for p in ['release','debug','asan','tsan'] for w in [1,2,8,16] for mt in [0,1]]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:rows=list(ex.map(job,tasks))
writecsv('results/mkv_safety.csv',rows)
