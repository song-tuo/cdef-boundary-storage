from checks import *
import re
rows=[]
for d,c in [(8,'420'),(10,'444'),(12,'444')]:
 stream=f's_w2_r19_{d}_{c}_c1'
 cases=[('clean',{})]+[(f'stage{i}',{'H1_FAULT_STAGE':str(i)}) for i in range(1,8)]+[(f'plane{i}',{'H1_ALLOC_PLANE':str(i)}) for i in range(3)]+[('owner',{'H1_ALLOC_OWNER':'1'})]
 for case,env in cases:
  tag=f'leaks_native_{d}_{c}_{case}';cmd=['/usr/bin/leaks','--atExit','--',ROOT/'builds/hybrid_audit_release/ivf_gate',ROOT/'inputs'/(stream+'.ivf'),'8','1'];r=run(tag,cmd,env=env|{'MallocStackLogging':'1'},timeout=60)
  text=(ROOT/'logs'/(tag+'.stdout')).read_text(errors='replace')+(ROOT/'logs'/(tag+'.stderr')).read_text(errors='replace');reports=re.findall(r'(\d+) leaks for (\d+) total leaked bytes',text)
  rows.append({'category':'leaks','profile':'release_audit','input':stream,'case':case,'tool_exit_code':r['exit_code'],'leak_reports':json.dumps(reports),'status':'PASS' if reports and all(a==b=='0' for a,b in reports) else 'FAIL' if reports else 'UNSUPPORTED_OR_NO_REPORT','command_log':tag})
writecsv('results/leak_native_safety.csv',rows)
