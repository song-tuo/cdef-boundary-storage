from checks import *
specs=json.loads((ROOT/'protocol/semantic_inputs.json').read_text());seq=json.loads((ROOT/'inputs/sequence_manifest.json').read_text());rows=list(csv.DictReader((ROOT/'semantic_matrix.csv').open()));schedule=json.loads((ROOT/'protocol/timing_schedule.json').read_text());cells=json.loads((ROOT/'protocol/timing_cells.json').read_text());checks={}
checks['semantic_rows']=len(rows)==2592;checks['semantic_no_failure']=all(r['status']=='PASS' for r in rows);checks['actual_cdef_worker_and_row_match']=all(r['coverage'] in ['OBSERVED','NO_CDEF_PATH'] for r in rows)
for v in ['type_fix','dual_token','hybrid']:
 vr=[r for r in rows if r['variant']==v and r['mode']=='audit'];enabled={s['id'] for s in specs if s['cdef_enabled']}|{s['id'] for s in seq};checks[v+'_enabled_cdef_path_coverage']=all(r['coverage']=='OBSERVED' for r in vr if r['input'] in enabled);checks[v+'_disabled_no_cdef_path']=all(r['coverage']=='NO_CDEF_PATH' for r in vr if r['input'] not in enabled)
 checks[v+'_same_instance_rows']=sum(r['input'].startswith('sequence_') for r in vr)==48
for c in cells:
 orders=Counter(tuple(b['order']) for b in schedule if b['cell_id']==c['cell_id']);checks[f'cell_{c["cell_id"]}_balanced_blocks']=len(orders)==6 and set(orders.values())=={2}
save(ROOT/'results/frozen_coverage_checks.json',checks);assert all(checks.values()),checks
print(len(checks),'frozen coverage checks PASS')
