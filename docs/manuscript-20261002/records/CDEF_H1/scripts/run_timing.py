from checks import *
import numpy as np
cells=json.loads((ROOT/'protocol/timing_cells.json').read_text());schedule=json.loads((ROOT/'protocol/timing_schedule.json').read_text());rows=[];warm=[]
seal=json.loads((ROOT/'protocol/TIMING_EXECUTION_SEAL.json').read_text());assert all(sha(ROOT/x['path'])==x['sha256'] for x in seal['files'])
assert all(sha(ROOT/'inputs'/(c['stream']+'.ivf'))==c['input_sha256'] for c in cells)
# Never drop observations, rerun blocks, change order or append samples.
for c in cells:
 for v in ['type_fix','dual_token','hybrid']:
  tag=f'timing_warm_c{c["cell_id"]}_{v}';x=execute(tag,v,'release',c['stream'],c['W_requested'],1);warm.append({'cell_id':c['cell_id'],'variant':v,'exit_code':x['exit_code'],'decode_ns':x['output'].get('decode_ns'),'pixel_sha256':x['output'].get('pixel_sha256'),'command_log':tag})
writecsv('results/timing_warmups.csv',warm)
for block in schedule:
 time.sleep(2);c=cells[block['cell_id']];values={};load_before=os.getloadavg()
 for pos,v in enumerate(block['order']):
  tag=f'timing_{block["block_id"]}_{v}';x=execute(tag,v,'release',c['stream'],c['W_requested'],1);values[v]=x
  rows.append({'block_id':block['block_id'],'cell_id':c['cell_id'],'replicate':block['replicate'],'order_position':pos,'order':','.join(block['order']),'variant':v,'family':c['family'],'width':c['width'],'height':c['height'],'W':c['W_requested'],'exit_code':x['exit_code'],'frames':x['output'].get('output_frames'),'pixel_sha256':x['output'].get('pixel_sha256'),'decode_ns':x['output'].get('decode_ns'),'load_1min_before_block':load_before[0],'load_5min_before_block':load_before[1],'load_15min_before_block':load_before[2],'status':'PASS' if clean(x) and x['output'].get('output_frames')==c['frames'] else 'FAIL','command_log':tag})
 eq=all(equality(values[v],values['type_fix']) for v in values)
 for r in rows[-3:]:r['block_hash_match']=eq
 writecsv('timing_blocks.csv',rows)
summary=[]
for c in cells:
 cellrows=[r for r in rows if r['cell_id']==c['cell_id']];blocks={}
 for r in cellrows:blocks.setdefault(r['block_id'],{})[r['variant']]=r
 ok=len(blocks)==12 and all(len(b)==3 and all(r['status']=='PASS' and r['block_hash_match'] for r in b.values()) for b in blocks.values());rng=np.random.default_rng(311000+c['cell_id']);ratios=np.array([b['hybrid']['decode_ns']/b['type_fix']['decode_ns'] for b in blocks.values()]);secondary=np.array([b['dual_token']['decode_ns']/b['hybrid']['decode_ns'] for b in blocks.values()]);ix=rng.integers(0,len(ratios),(50000,len(ratios)));boots=np.median(ratios[ix],axis=1);lo,hi=np.quantile(boots,[.025,.975]);slo,shi=np.quantile(np.median(secondary[ix],axis=1),[.025,.975]);status='PASS_LOCAL_NONINFERIORITY' if ok and hi<=1.02 else 'EXPLICIT_LOCAL_REGRESSION' if ok and lo>1.02 else 'INCONCLUSIVE_LOCAL_NONINFERIORITY' if ok else 'INCOMPLETE'
 summary.append({**c,'blocks':len(blocks),'hybrid_type_fix_median':float(np.median(ratios)),'ci95_low':float(lo),'ci95_high':float(hi),'dual_token_hybrid_median':float(np.median(secondary)),'secondary_ci95_low':float(slo),'secondary_ci95_high':float(shi),'bootstrap_unit':'complete_three_variant_block','bootstrap_replicates':50000,'bootstrap_seed':311000+c['cell_id'],'status':status})
writecsv('timing_summary.csv',summary)
