from checks import *
import concurrent.futures
specs=json.loads((ROOT/'protocol/semantic_inputs.json').read_text());seq=json.loads((ROOT/'inputs/sequence_manifest.json').read_text());tasks=[]
for s in specs:
 for mt in [0,1]:tasks.append((s,s['W_requested'],mt))
for s in seq:
 for w in [1,2,8,16]:
  for mt in [0,1]:tasks.append((s,w,mt))
def job(t):
 s,w,mt=t;outputs={};rows=[]
 for mode in ['release','audit']:
  for v in ['type_fix','dual_token','hybrid']:
   tag=f'sem_{mode}_{s["id"]}_w{w}_m{mt}_{v}';variant=v if mode=='release' else v+'_audit';x=execute(tag,variant,'release',s['id'],w,mt);outputs[(mode,v)]=x
   ref=outputs[(mode,'type_fix')];ok=clean(x,mode=='audit') and equality(x,ref) and x['output'].get('output_frames')==s['frames']
   ok &= x['output'].get('bit_depth')==s['depth'] and x['output'].get('subsampling_x')==(1 if s['chroma']=='420' else 0) and x['output'].get('subsampling_y')==(1 if s['chroma']=='420' else 0)
   if mode=='audit':ok &= x['copy_hash']==ref['copy_hash'] and equality(x,outputs[('release',v)])
   ev=[e for e in x['events'] if e.get('h1')=='frame_begin'];actualW=sorted(set(e['workers'] for e in ev));actualR=sorted(set(e['rows'] for e in ev))
   coverage='OBSERVED' if ev else 'NO_CDEF_PATH'
   if mode=='audit' and ev and actualW!=[w]:coverage='ACTUAL_WORKER_MISMATCH'
   if mode=='audit' and 'R' in s and ev and actualR!=[s['R']]:coverage='ACTUAL_ROW_MISMATCH'
   rows.append({'coverage':coverage,'input':s['id'],'variant':v,'mode':mode,'W_requested':w,'row_mt':mt,'actual_W':json.dumps(actualW),'actual_R':json.dumps(actualR),'exit_code':x['exit_code'],'frames':x['output'].get('output_frames'),'visible_frame_hashes':json.dumps(x['visible_hashes'],separators=(',',':')),'pixel_sha256':x['output'].get('pixel_sha256'),'copy_sequence_sha256':x['copy_hash'],'copy_frames':x['copy_frames'],'allocation_double':x['double_allocation'],'free_double':x['double_free'],'unreleased_allocations':x['unreleased_allocations'],'slot_collision_invalid_owner':x['slot_violations'],'exhaustion':x['exhaustion'],'ordering_errors':x['order_errors'],'sanitizer':x['sanitizer'],'status':'PASS' if ok else 'FAIL','command_log':tag})
 save(ROOT/'results/semantic_cases'/(s['id']+f'_w{w}_m{mt}.json'),rows)
 return rows
allrows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for rr in ex.map(job,tasks):
  allrows+=rr
  if len(allrows)%120==0:print('SEMANTIC_ROWS',len(allrows),flush=True)
writecsv('semantic_matrix.csv',allrows)
save(ROOT/'results/semantic_summary.json',{'rows':len(allrows),'failed':sum(x['status']!='PASS' for x in allrows),'inputs':len(tasks),'stage':'2'})
print('SEMANTICS COMPLETE',len(allrows),'failures',sum(x['status']!='PASS' for x in allrows))
