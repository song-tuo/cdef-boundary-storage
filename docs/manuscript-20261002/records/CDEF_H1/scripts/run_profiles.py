from checks import *
import concurrent.futures
specs=json.loads((ROOT/'protocol/semantic_inputs.json').read_text());seq=json.loads((ROOT/'inputs/sequence_manifest.json').read_text());tasks=[]
for p in ['debug','asan','tsan']:
 for s in specs:
  for mt in [0,1]:tasks.append((p,s,s['W_requested'],mt))
 for s in seq:
  for w in [1,2,8,16]:
   for mt in [0,1]:tasks.append((p,s,w,mt))
def job(t):
 p,s,w,mt=t;tag=f'safety_{p}_{s["id"]}_w{w}_m{mt}';x=execute(tag,'hybrid',p,s['id'],w,mt)
 ref=parse(f'sem_release_{s["id"]}_w{w}_m{mt}_type_fix');ok=clean(x) and equality(x,ref)
 return {'category':'decoder_matrix','profile':p,'input':s['id'],'W':w,'row_mt':mt,'exit_code':x['exit_code'],'frames':x['output'].get('output_frames'),'pixel_sha256':x['output'].get('pixel_sha256'),'sanitizer':x['sanitizer'],'status':'PASS' if ok else 'FAIL','command_log':tag}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 rows=list(ex.map(job,tasks))
writecsv('results/safety_profiles.csv',rows);save(ROOT/'results/safety_profile_summary.json',{'rows':len(rows),'failed':sum(x['status']!='PASS' for x in rows)})
