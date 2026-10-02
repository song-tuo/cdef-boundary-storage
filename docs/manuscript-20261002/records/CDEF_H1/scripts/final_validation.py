from checks import *
import xml.etree.ElementTree as ET
checks={}
blocks=list(csv.DictReader((ROOT/'timing_blocks.csv').open()));schedule=json.loads((ROOT/'protocol/timing_schedule.json').read_text());checks['648_timed_processes']=len(blocks)==648;checks['216_complete_blocks']=len(set(r['block_id'] for r in blocks))==216;checks['all_timing_hashes_match']=all(r['block_hash_match']=='True' for r in blocks);checks['all_timing_exits_zero']=all(r['exit_code']=='0' for r in blocks)
checks['frozen_order_exact']=all([r['variant'] for r in blocks if r['block_id']==s['block_id']]==s['order'] for s in schedule)
checks['all_timing_input_hashes_preserved']=all(sha(ROOT/'inputs'/(s['stream']+'.ivf'))==s['input_sha256'] for s in json.loads((ROOT/'protocol/timing_cells.json').read_text()))
lineage=json.loads((ROOT/'inputs/source_input_manifest.json').read_text());checks['prior_sources_read_only']=all(sha(r['original'])==r['sha256'] for r in lineage)
fixtures=json.loads((ROOT/'inputs/upstream_fixture_manifest.json').read_text());bad=[]
for r in fixtures:
 h=hashlib.sha256()
 with Path(r['source_path']).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 if h.hexdigest()!=r['sha256']:bad.append(r['name'])
checks['prior_572_official_fixtures_read_only']=not bad
save(ROOT/'results/final_fixture_preservation.json',{'verified_files':len(fixtures),'mismatches':bad})
checks['source_input_binary_seal_unchanged']=not json.loads((ROOT/'results/final_seal_recheck.json').read_text())['changed']
checks['independent_pixel_byte_formula']=all(r['pass'] for r in json.loads((ROOT/'results/allocation_formula_check.json').read_text()))
checks['FPMT_multithread_reached']=all(r['pass'] for r in json.loads((ROOT/'results/fpmt_path_coverage.json').read_text()))
checks['FPMT_full_library_instrumented']=all(r['pass'] for r in json.loads((ROOT/'results/fpmt_instrumentation_audit.json').read_text()))
required=['SOURCE_DRIFT_AUDIT.md','PROTOCOL_FROZEN.md','HYBRID_DESIGN.md','THEORY_CHECK.md','semantic_matrix.csv','safety_matrix.csv','fault_recovery.csv','allocation_accounting.csv','timing_blocks.csv','timing_summary.csv','real_content.csv','PATCH_LEDGER.md','RESULTS.md','decision.json']
checks['requested_artifacts_before_package']=all((ROOT/n).is_file() for n in required)
save(ROOT/'results/final_validation.json',checks);assert all(checks.values()),checks
print(len(checks),'final validation checks PASS; old source and all 572 official fixtures unchanged')
