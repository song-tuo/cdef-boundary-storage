from checks import *
cells=json.loads((ROOT/'protocol/timing_cells.json').read_text());rows=[]
for c in cells:
 outputs={}
 for v in ['type_fix','dual_token','hybrid']:
  tag=f'timing_audit_c{c["cell_id"]}_{v}';x=execute(tag,v+'_audit','release',c['stream'],c['W_requested'],1);outputs[v]=x;ref=outputs['type_fix'];activity=[e for e in x['events'] if e.get('h1')=='activation'];fb=[e for e in x['events'] if e.get('h1')=='frame_begin'];ok=clean(x,True) and equality(x,ref) and x['copy_hash']==ref['copy_hash'] and x['output'].get('output_frames')==c['frames'] and bool(activity) and sorted(set(e['workers'] for e in fb))==[c['W_requested']]
  rows.append({'cell_id':c['cell_id'],'variant':v,'actual_W':json.dumps(sorted(set(e['workers'] for e in fb))),'cdef_frames':len(fb),'activation_calls':len(activity),'nonzero_strength_calls':sum(e['primary']!=0 or e['secondary']!=0 for e in activity),'pixel_sha256':x['output'].get('pixel_sha256'),'copy_sha256':x['copy_hash'],'status':'PASS' if ok else 'FAIL','command_log':tag})
writecsv('results/timing_activity.csv',rows)
save(ROOT/'protocol/TIMING_EXECUTION_SEAL.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [ROOT/'scripts/run_timing.py',ROOT/'protocol/timing_cells.json',ROOT/'protocol/timing_schedule.json',ROOT/'protocol/protocol.json']]+[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [ROOT/'builds'/f'{v}_release'/'ivf_gate' for v in ['type_fix','dual_token','hybrid']]]})
