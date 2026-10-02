from checks import *
account=list(csv.DictReader((ROOT/'allocation_accounting.csv').open()));base={(r['width'],r['height'],r['W_requested']):r for r in account if r['variant']=='type_fix'}
for r in account:
 b=base[(r['width'],r['height'],r['W_requested'])];R=int(r['R']);W=int(r['actual_W']);r['row_index_metadata_bytes']=0 if r['variant']=='type_fix' else R*2*4;r['base_row_sync_requested_bytes']=int(r['row_struct_requested'])-r['row_index_metadata_bytes'];r['worker_added_logical_field_bytes']=W*4 if r['variant']=='hybrid' else 0;r['worker_added_layout_bytes']=int(r['worker_requested'])-int(b['worker_requested']);r['sync_layout_increment_bytes']=int(r['sync_struct_bytes'])-int(b['sync_struct_bytes']);r['pixel_saved_vs_type_fix_requested_bytes']=int(b['pixel_requested'])-int(r['pixel_requested']);r['pixel_saved_fraction']=1-int(r['pixel_requested'])/int(b['pixel_requested']);r['pixel_boundary_metric']='requested + actual backing-block usable; not RSS/SRAM/area/energy'
writecsv('results/allocation_details.csv',account)
rows=list(csv.DictReader((ROOT/'real_content.csv').open()))
for r in rows:
 x=parse(r['command_log']);ev=[e for e in x['events'] if e.get('h1')=='activation' and e['plane']==0];nonzero=[e for e in ev if e['primary'] or e['secondary']];frames=[e for e in x['events'] if e.get('h1')=='visible_frame'];denom=sum(((e['width']+7)//8)*((e['height']+7)//8) for e in frames)
 r['nonzero_strength_luma_calls']=len(nonzero);r['nonzero_strength_luma_blocks']=sum(e['blocks'] for e in nonzero);r['visible_luma_8x8_cells']=denom;r['nonzero_luma_fraction']=r['nonzero_strength_luma_blocks']/denom if denom else None;r['direction_only_luma_blocks']=sum(e['blocks'] for e in ev if not(e['primary'] or e['secondary']))
writecsv('results/real_content_activity_details.csv',rows)
