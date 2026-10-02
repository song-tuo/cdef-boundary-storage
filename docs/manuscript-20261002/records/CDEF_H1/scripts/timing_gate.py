from common import *
import csv
# All task-owned CPU work must finish before prospective timing; no overlap with safety/builds.
prerequisites=['022_safety_profiles','023_fault_recovery','024_allocation','025_upstream','026_fpmt','027_real_content','028_mkv','030_leaks_native','031_timing_activity','032_evidence_audit','033_derived_accounting_content','034_patch_ledger','035_upstream_shell','038_fixture_cache','039_coverage','040_allocation_formula','041_fpmt_sanitizers','042_fpmt_instrumentation','043_fpmt_coverage']
while not all((ROOT/'logs'/(n+'.result.json')).exists() for n in prerequisites):time.sleep(5)
assert all(json.loads((ROOT/'logs'/(n+'.result.json')).read_text())['exit_code']==0 for n in prerequisites)
up=list(csv.DictReader((ROOT/'results/upstream_safety.csv').open()));assert all(int(r['exit_code'])==0 for r in up),'Nonzero upstream result needs inspection; timing not started'
for name in ['semantic_matrix.csv','results/timing_activity.csv','real_content.csv','results/mkv_safety.csv']:
 assert all(r['status']=='PASS' for r in csv.DictReader((ROOT/name).open())),'Semantic failure: timing not started'
print('All safety/build processes completed; settling 55 seconds before warmups.',flush=True)
time.sleep(55)
raise SystemExit(run('045_timing',['python3',ROOT/'scripts/run_timing.py'])['exit_code'])
