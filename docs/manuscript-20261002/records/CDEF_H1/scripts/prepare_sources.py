from common import *
import shutil,difflib
old=ROOT.parent/'CDEF_full_source_gate';rec=[]
for v,origin in [('type_fix','type_fix'),('dual_token','token'),('hybrid','token')]:
 src=ROOT/'src'/v;shutil.copytree(old/'src'/origin,src,dirs_exist_ok=True)
 for p in sorted(src.rglob('*')):
  if p.is_file():rec.append({'variant':v,'relative_path':str(p.relative_to(src)),'original':str(old/'src'/origin/p.relative_to(src)),'sha256':sha(p)})
save(ROOT/'inputs/source_input_manifest.json',rec)
for n in ['baseline_to_type_fix.patch','type_fix_to_token.patch']:shutil.copyfile(old/'patches'/n,ROOT/'patches'/n)
for n in ['ivf_gate.c','generate_workloads.py','ownership_model.py','run_mkv_conformance.py']:
 shutil.copyfile(old/'scripts'/n,ROOT/'history'/n)
s=ROOT/'src/hybrid'
def edit(name,old,new):
 p=s/name;t=p.read_text();assert t.count(old)==1,(name,old[:80],t.count(old));p.write_text(t.replace(old,new))
for name in ['av1/common/alloccommon.c','av1/common/thread_common.c','av1/common/thread_common.h']:
 p=s/name;p.write_text(p.read_text().replace('boundary_owner','top_owner'))
edit('av1/common/alloccommon.c','aom_calloc(strips, sizeof(*cdef_sync->top_owner))','aom_calloc(top_slots, sizeof(*cdef_sync->top_owner))')
edit('av1/common/thread_common.h','  cdef_init_fb_row_t cdef_init_fb_row_fn;\n  int do_extend_border;','  cdef_init_fb_row_t cdef_init_fb_row_fn;\n  int do_extend_border;\n  // Persistent worker-local bottom slot; -1 selects direct short-frame indexing.\n  int bottom_worker_slot;')
edit('av1/common/thread_common.h','''  // Pool entries contain the consuming row, or -1 when free. The existing
  // job mutex protects ownership; pixel copies retain the row-sync contract.''','''  // Top-only dynamic ownership. Bottom storage has no owner array or free scan.
  // The existing job mutex protects top reservation/release.''')
edit('av1/common/thread_common.c','''  if (row < rows - 1) {
    const int slot = sync->cdef_row_mt[row].bottom_slot;
    assert(slot >= 0 && slot < sync->bottom_slots);
    assert(sync->top_owner[sync->top_slots + slot] == row);
    sync->top_owner[sync->top_slots + slot] = -1;
  }''','''  (void)rows;
  // Bottom is worker-private (or unique to the row in a short frame).
  // Worker sequential execution ends its lifetime here; no pool state to free.''')
edit('av1/common/thread_common.c','''volatile int *cur_fbr, const int nvfb) {''','''volatile int *cur_fbr, const int nvfb,
                                        const int bottom_worker_slot) {''')
edit('av1/common/thread_common.c','''      const int bottom = cdef_take_boundary(
          cdef_sync->top_owner + cdef_sync->top_slots,
          cdef_sync->bottom_slots, *cur_fbr);
      if (top < 0 || bottom < 0) {''','''      const int bottom = bottom_worker_slot >= 0 ? bottom_worker_slot : *cur_fbr;
      if (top < 0 || bottom < 0 || bottom >= cdef_sync->bottom_slots) {''')
edit('av1/common/thread_common.c','get_cdef_row_next_job(cdef_sync, &cur_fbr, nvfb)','get_cdef_row_next_job(cdef_sync, &cur_fbr, nvfb,\n                                              cdef_worker->bottom_worker_slot)')
edit('av1/common/thread_common.c','''    cdef_worker[i].cm = cm;''','''    cdef_worker[i].bottom_worker_slot =
        cm->cdef_info.allocated_mi_rows - 1 >= num_workers ? i : -1;
    cdef_worker[i].cm = cm;''')
p=s/'av1/common/thread_common.c';t=p.read_text().replace('cdef_sync->top_slots + cdef_sync->bottom_slots','cdef_sync->top_slots');p.write_text(t)
patch=[]
for p in sorted(s.rglob('*')):
 if not p.is_file():continue
 oldp=ROOT/'src/dual_token'/p.relative_to(s)
 if p.read_bytes()!=oldp.read_bytes():patch+=list(difflib.unified_diff(oldp.read_text().splitlines(True),p.read_text().splitlines(True),'dual_token/'+str(p.relative_to(s)),'hybrid/'+str(p.relative_to(s))))
(ROOT/'patches/dual_token_to_hybrid.patch').write_text(''.join(patch))
# Verify every arithmetic/DSP source is untouched and copy call count unchanged.
for rel in ['av1/common/cdef.c','av1/common/cdef_block.c','av1/common/cdef_block.h']:
 assert sha(s/rel)==sha(ROOT/'src/type_fix'/rel)
for v in ['dual_token','hybrid']:
 assert (ROOT/f'src/{v}/av1/common/thread_common.c').read_text().count('av1_cdef_copy_sb8_16(')==2
assert (s/'av1/common/thread_common.c').read_text().count('cdef_take_boundary(')==2
print('Independent source trees prepared; hybrid bottom owner/scan removed; arithmetic and copy-site count unchanged')
