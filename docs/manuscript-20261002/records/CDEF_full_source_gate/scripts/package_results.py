from pathlib import Path
import json,shutil,hashlib,zipfile,datetime
root=Path(__file__).resolve().parents[1]
assert (root/'decision.json').exists()
assert len(json.loads((root/'results/timing_results.json').read_text()))==312
pkg=root/'return_package';pkg.mkdir(exist_ok=True)
for name in ['scripts','protocol','patches','maintainability','prior_work','logs','results']:
    shutil.copytree(root/name,pkg/name,dirs_exist_ok=True)
for name in ['RESULTS.md','decision.json','source_identity.json']:
    shutil.copy2(root/name,pkg/name)
for name in ['upstream_tag_refs.txt','upstream_commit_tree.txt','upstream_git_tree.txt']:
    shutil.copy2(root/'downloads'/name,pkg/'source_archives'/name)
shutil.copytree(root/'testdata/generated',pkg/'testdata/generated',dirs_exist_ok=True)
for p in (root/'testdata').glob('*'):
    if p.is_file() and ('.md5' in p.name or '.res' in p.name):
        shutil.copy2(p,pkg/'testdata'/p.name)
groups={
 'correctness':['output_hash_comparison_release.csv','correctness_release.json','correctness_debug.json','correctness_asan.json','correctness_tsan.json','invalid_input_comparison.json','mkv_conformance.json'],
 'memory':['memory_results.csv','memory_results.json'],
 'timing':['timing_results.csv','timing_results.json','timing_summary.json','timing_calibration.json'],
 'tests':['testdata_manifest.json','final_upstream_summary.json','row_tiles_retry_status.json','fpmt_large_status.json','shell_decode.json'],
 'sanitizers':['instrumentation_audit.json','leak_checks.json','sanitizer_optional_interruption.json'],
 'fault_injection':['fault_injection.json','fault_injection_tsan.json','same_instance_recovery_asan.json','same_instance_recovery_tsan.json'],
}
for group,names in groups.items():
    (pkg/group).mkdir(exist_ok=True)
    for name in names:shutil.copy2(root/'results'/name,pkg/group/name)
shutil.copy2(root/'results/output_hash_comparison_release.csv',pkg/'correctness/output_hash_comparison.csv')
for p in (root/'builds').iterdir():
    if not p.is_dir():continue
    target=pkg/'build'/p.name;target.mkdir(parents=True,exist_ok=True)
    for name in ['CMakeCache.txt','compile_commands.json','config/aom_config.h','config/aom_version.h']:
        if (p/name).exists():
            q=target/name;q.parent.mkdir(exist_ok=True);shutil.copy2(p/name,q)
    # Preserve the exact frozen, already measured binaries separately from rebuildable objects.
    if p.name in ['baseline_release','type_fix_release','token_release']:
        target=pkg/'builds'/p.name;target.mkdir(parents=True,exist_ok=True)
        for name in ['ivf_gate','libaom.a','aomdec','aomenc']:shutil.copy2(p/name,target/name)
manifest=[]
for p in sorted(pkg.rglob('*')):
    if p.is_file() and p.name!='manifest.json':
        manifest.append(dict(path=str(p.relative_to(pkg)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(pkg/'manifest.json').write_text(json.dumps({'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Every file in this return package except this self-referential manifest. The ZIP container checksum is stored beside the archive. Original large upstream test media and rebuildable object directories remain in the workspace and are identified by separate manifests.','files':manifest},indent=2)+'\n')
archive=root/'CDEF_full_source_gate_return.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(pkg.rglob('*')):
        if p.is_file():z.write(p,Path('CDEF_full_source_gate_return')/p.relative_to(pkg))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
h=hashlib.sha256(archive.read_bytes()).hexdigest()
(root/'CDEF_full_source_gate_return.zip.sha256').write_text(h+'  '+archive.name+'\n')
shutil.copy2(pkg/'manifest.json',root/'manifest.json')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':h,'manifest_files':len(manifest)},indent=2))
