from checks import *
rows=[]
for width,height in [(1920,1080),(2560,1440),(3840,2160)]:
 for w in [2,8,16]:
  for v in ['type_fix','dual_token','hybrid']:
   tag=f'account_{v}_{width}x{height}_w{w}';x=execute(tag,v+'_account','release',f'alloc_{width}x{height}',w,1);events=[e for e in x['events'] if e.get('h1')=='account'];e=events[-1] if events else {};R=e.get('rows',0);actualW=e.get('workers',0);top=min(R-1,w+1);bottom=min(R-1,w)
   ok=clean(x) and bool(events) and actualW==w and R==(height+63)//64
   if v!='type_fix':ok &= e.get('top_slots')==top and e.get('bottom_slots')==bottom
   if v=='hybrid':ok &= e.get('owner_requested')==top*4
   pad=sum(e.get(k+'_usable',0)-e.get(k+'_requested',0) for k in ['pixel','owner','row_struct','worker'])
   rows.append({'variant':v,'width':width,'height':height,'W_requested':w,'actual_W':actualW,'R':R,'theoretical_top':top,'theoretical_bottom':bottom,'theoretical_total':min(2*R-2,2*w+1),'allocator_padding_charged_categories':pad,**{k:val for k,val in e.items() if k not in ['h1','width','height','workers','rows']},'status':'PASS' if ok else 'FAIL','command_log':tag})
writecsv('allocation_accounting.csv',rows)
