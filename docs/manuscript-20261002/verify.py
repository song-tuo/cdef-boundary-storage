"""Integrity and manuscript-selection checks only; runs no experiment/statistics."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json

ROOT = Path(__file__).parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((ROOT/'MANIFEST.json').read_text())
for x in manifest['files']:
    p=ROOT/x['path']
    assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'],x['path']

def rows(p): return list(csv.DictReader((ROOT/p).open()))
for x in rows('EVIDENCE_MAP.csv'):
    for name in x['evidence_files'].split('; '):
        if not (ROOT/name).exists():
            assert name in manifest.get('release_only_files',[]),name
alloc=rows('records/CDEF_H1/allocation_accounting.csv')
for width,w,expected in [(1920,8,(510,255)),(1920,16,(510,480)),(3840,8,(2040,510)),(3840,16,(2040,990))]:
    found={x['variant']:x for x in alloc if int(x['width'])==width and int(x['W_requested'])==w}
    assert tuple(int(found[v]['pixel_requested'])//1024 for v in ['type_fix','dual_token'])==expected
assert sha(ROOT/'RESOURCE_ACCOUNTING.csv')==sha(ROOT/'records/CDEF_H1/allocation_accounting.csv')
assert sha(ROOT/'HISTORICAL_PROCESS_MEMORY.csv')==sha(ROOT/'records/CDEF_full_source_gate/results/memory_results.csv')
assert len(rows('HISTORICAL_PROCESS_MEMORY.csv'))==90
raw=rows('records/CDEF_H1/timing_blocks.csv')
assert len(raw)==648
counts=Counter(x['block_id'] for x in raw)
assert len(counts)==216 and set(counts.values())=={3}
timing=rows('records/CDEF_FINAL_PAPER_GATE/TIMING_REANALYSIS.csv')
assert len(timing)==54
primary=[x for x in timing if x['contrast']=='hybrid/type_fix']
assert Counter(x['status'] for x in primary)=={'PASS_LOCAL_NONINFERIORITY':6,'INCONCLUSIVE_LOCAL_NONINFERIORITY':12}
secondary=[x for x in timing if x['contrast']=='dual_token/type_fix']
assert all(x['analysis_role']=='secondary_descriptive' and x['status']=='SECONDARY_DESCRIPTIVE_NO_GATE' for x in secondary)
assert all(float(x['ci95_low'])<=1<=float(x['ci95_high']) for x in secondary)
assert len(rows('records/CDEF_FINAL_PAPER_GATE/reanalysis/block_ratios.csv'))==648
assert json.loads((ROOT/'records/CDEF_H1/decision.json').read_text())['final_state']=='KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT'
for name,n in [('correctness_release',540),('correctness_debug',180),('correctness_asan',180),('correctness_tsan',180),('fault_injection',156),('fault_injection_tsan',156),('same_instance_recovery_asan',99),('same_instance_recovery_tsan',99),('leak_checks',36)]:
    assert len(json.loads((ROOT/f'records/CDEF_full_source_gate/results/{name}.json').read_text()))==n
assert len(rows('records/CDEF_H1/semantic_matrix.csv'))==2592
assert len(rows('records/CDEF_H1/real_content.csv'))==81
print(json.dumps({'status':'PASS','manifest_files':len(manifest['files']),'H1_blocks':216,'H1_timed_processes':648,'primary_pass':6,'primary_inconclusive':12,'new_experiments':0,'new_estimates_or_intervals':0},indent=2))
