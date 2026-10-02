from checks import *
import concurrent.futures
specs=json.loads((ROOT/'inputs/real_encoded_manifest.json').read_text())
def job(t):
 s,w=t;sid=s['id'];outputs={};rows=[]
 for v in ['type_fix','dual_token','hybrid']:
  tag=f'real_{sid}_w{w}_{v}';x=execute(tag,v+'_audit','release',sid,w,1);outputs[v]=x;ref=outputs['type_fix'];activity=[e for e in x['events'] if e.get('h1')=='activation' and e.get('plane')==0];fb=[e for e in x['events'] if e.get('h1')=='frame_begin'];ok=clean(x,True) and equality(x,ref) and x['copy_hash']==ref['copy_hash']
  canonical=[{k:e[k] for k in ['row','col','plane','blocks','primary','secondary']} for e in activity];activity_hash=hashlib.sha256(json.dumps(sorted(canonical,key=lambda e:tuple(e.values())),sort_keys=True).encode()).hexdigest()
  rows.append({'input':sid,'variant':v,'W_requested':w,'actual_W':json.dumps(sorted(set(e['workers'] for e in fb))),'frames':x['output'].get('output_frames'),'pixel_sha256':x['output'].get('pixel_sha256'),'copy_sha256':x['copy_hash'],'filtered_luma_calls':len(activity),'filtered_luma_blocks':sum(e['blocks'] for e in activity),'strengths':json.dumps(sorted(set((e['primary'],e['secondary']) for e in activity))),'activation_sha256':activity_hash,'exit_code':x['exit_code'],'status':'PASS' if ok else 'FAIL','command_log':tag})
 return rows
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for rr in ex.map(job,[(s,w) for s in specs for w in [2,8,16]]):rows+=rr
writecsv('real_content.csv',rows)
