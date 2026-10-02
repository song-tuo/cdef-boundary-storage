from checks import *
import concurrent.futures
cases=[(f'stage{s}',{'H1_FAULT_STAGE':str(s)}) for s in range(1,8)]+[(f'plane{p}',{'H1_ALLOC_PLANE':str(p)}) for p in range(3)]+[('owner',{'H1_ALLOC_OWNER':'1'}),('negative_stage',{'H1_FAULT_STAGE':'99'}),('negative_row',{'H1_FAULT_STAGE':'2','H1_FAULT_ROW':'9999'})]
save(ROOT/'protocol/fault_execution.json',{'input_R':19,'source_inputs':'s_w2_r19_{depth}_{chroma}_c1.ivf','cases':cases,'rationale':'frozen generated inputs; R>W for every tested W, target row 1 exists; no production changes'})
tasks=[(p,d,c,w) for p in ['asan','tsan'] for d in [8,10,12] for c in ['420','444'] for w in [2,8,16]]
def job(t):
 p,d,c,w=t;stream=f's_w2_r19_{d}_{c}_c1';base=f'fault_{p}_{d}_{c}_w{w}';ref=execute(base+'_reference','type_fix','release',stream,w,1);rows=[]
 for case,env in cases:
  negative=case.startswith('negative');tag=base+'_'+case
  for mode,harness in [('fault','ivf_gate')]+([] if negative else [('same_instance','ivf_recovery'),('destroy_recreate','ivf_recreate')]):
   log=tag+'_'+mode;x=execute(log,'hybrid_audit',p,stream,w,1,env,harness,60)
   expected=0 if negative or mode!='fault' else 3
   faults=sum(e.get('h1')=='fault' for e in x['events']);errors=[e for e in x['events'] if e.get('h1')=='same_instance_recovery'];recreate=[e for e in x['events'] if e.get('h1')=='destroy_recreate']
   ok=x['exit_code']==expected and x['output'].get('destroy_status')==0 and not(x['sanitizer'] or x['slot_violations'] or x['exhaustion'] or x['double_allocation'] or x['double_free'] or x['unreleased_allocations'])
   if case.startswith('stage'):ok &= faults==1
   if mode=='fault' and (case.startswith('plane') or case=='owner'):ok &= x['output'].get('status')==2
   if mode=='same_instance':ok &= len(errors)==1 and equality(x,ref)
   if mode=='destroy_recreate':ok &= len(recreate)==1 and recreate[0]['first_exit']==3 and equality(x,ref)
   if negative:ok &= clean(x,True) and equality(x,ref) and faults==0
   rows.append({'profile':p,'depth':d,'chroma':c,'W':w,'case':case,'mode':mode,'exit_code':x['exit_code'],'codec_status':x['output'].get('status'),'frames':x['output'].get('output_frames'),'fault_events':faults,'recovery_events':len(errors)+len(recreate),'sanitizer':x['sanitizer'],'slot_violations':x['slot_violations'],'exhaustion':x['exhaustion'],'double_allocation':x['double_allocation'],'double_free':x['double_free'],'unreleased_allocations':x['unreleased_allocations'],'status':'PASS' if ok else 'FAIL','command_log':log})
 save(ROOT/'results/fault_cases'/(base+'.json'),rows);return rows
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for r in ex.map(job,tasks):rows+=r
writecsv('fault_recovery.csv',rows);save(ROOT/'results/fault_summary.json',{'rows':len(rows),'failed':sum(r['status']!='PASS' for r in rows)})
