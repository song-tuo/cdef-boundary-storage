from common import *
import platform
ident=json.loads((ROOT/'results/source_identity.json').read_text())
lines=['# Source drift audit','', 'Official source: https://aomedia.googlesource.com/aom . Git fetches, commit identities, full archive exports and independently recomputed Git blob identities are in logs/003–006 and results/source_identity.json. Current main is pinned at audit time, not a moving claim.','', '## Finding','', 'None of the three revisions implements equivalent worker-bounded pre-filter boundary storage. All retain frame-row-indexed MT line buffers. Stage 0 does not stop H1.','', 'For all three revisions: R = ceil(mi_rows/MI_SIZE_64X64); the decoder passes its allocated CDEF worker count (num_workers, W), not the instantaneous number of busy workers. The existing job mutex issues monotonically increasing row jobs. A row copies its outgoing top boundary and its own bottom boundary, signals that copy completion, waits for the preceding row copy, then filters in place. The predecessor copy is what preserves the consumer\'s pre-filter pixels.','', 'Upstream MT allocation per plane is sizeof(*cdef_info->linebuf) × R × (CDEF_VBORDER << 1) × stride. Because linebuf is an array of pointers, this sizeof is pointer width, not sample width. The frozen type_fix changes this single sample-size expression to sizeof(**cdef_info->linebuf); the storage remains row-indexed. Upstream top addressing is row × border × stride; bottom base is R × border × stride and bottom row addressing is likewise row-indexed.','', 'W=1 uses the unchanged serial ping-pong path. Its legacy allocation is outside the H1 tight MT capacity acceptance, as explicitly confirmed by the user. The encoder uses the same common CDEF synchronization/worker structures, so its frame-parallel path requires an independent hybrid safety check.','', '## Source evidence (line numbers refer to exported files)','']
for version in ['v3.12.1','v3.15.1','main']:
 rs=[r for r in ident if r['version']==version];lines+=['### '+version+' — '+rs[0]['commit'],'','| Source | Git blob | SHA-256 |','|---|---|---|']
 for r in rs:lines += [f"| {r['path']} | {r['git_blob']} | {r['sha256']} |"]
 lines+=['','Relevant anchors:']
 for path in ['av1/common/alloccommon.c','av1/common/thread_common.c','av1/decoder/decodeframe.c']:
  for i,line in enumerate((ROOT/'upstream'/version/path).read_text().splitlines(),1):
   if any(s in line for s in ['sizeof(*cdef_info->linebuf)','const int num_bufs','cdef_row_mt_sync_write(cdef_sync, fbr)','cdef_row_mt_sync_read(cdef_sync, fbr)','av1_cdef_frame_mt(','av1_cdef_alloc_data(','uint16_t *bot_linebuf =','uint16_t *top_linebuf =']):lines.append(f'- `{version}/{path}:{i}`: `{line.strip()}`')
 lines+=['']
(ROOT/'SOURCE_DRIFT_AUDIT.md').write_text('\n'.join(lines)+'\n')
files=[]
for area in ['src','inputs','protocol','scripts']:
 for p in sorted((ROOT/area).rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
for p in sorted((ROOT/'builds').glob('*/*')):
 if p.name in ['libaom.a','aomdec','aomenc','test_libaom','ivf_gate','ivf_recovery','ivf_recreate','compile_commands.json','CMakeCache.txt'] and p.is_file():files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
output=ROOT/'protocol/IMPLEMENTATION_SEAL.json';assert not output.exists()
save(output,{'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'before_first_H1_scientific_decoder_run':True,'platform':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'files':files})
print('SEALED',len(files),'files',sha(output))
