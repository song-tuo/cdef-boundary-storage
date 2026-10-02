from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
for variant in ['baseline','type_fix','token']:
    src=root/'src'/f'{variant}_audit'
    shutil.copytree(root/'src'/variant,src)
    def edit(name,old,new):
        p=src/name;s=p.read_text();assert s.count(old)==1,(name,old[:60],s.count(old));p.write_text(s.replace(old,new))
    edit('av1/common/thread_common.h','  int is_row_done;', '''  uint64_t gate_wait_ns;
  struct aom_internal_error_info *gate_error;
  int is_row_done;''')
    edit('av1/common/thread_common.h','  bool cdef_mt_exit;', '''  int gate_fault_fired;
  bool cdef_mt_exit;''')
    header='''#ifndef CDEF_GATE_AUDIT_H_
#define CDEF_GATE_AUDIT_H_
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <malloc/malloc.h>
static inline uint64_t cdef_gate_now(void) {
  struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return (uint64_t)t.tv_sec * 1000000000 + t.tv_nsec;
}
// Mirrors aom_mem.c's GetActualMallocAddress; measures the allocator block,
// including alignment padding, NOT malloc_size on an interior aligned pointer.
static inline size_t cdef_gate_usable(void *p) {
  return p ? malloc_size((void *)(((size_t *)p)[-1])) : 0;
}
static inline int cdef_gate_env(const char *name, int fallback) {
  const char *s=getenv(name); return s ? atoi(s) : fallback;
}
#endif
'''
    (src/'av1/common/cdef_gate_audit.h').write_text(header)
    for name in ['av1/common/alloccommon.c','av1/common/thread_common.c','av1/decoder/decodeframe.c']:
        p=src/name;s=p.read_text();idx=s.index('#include');s=s[:idx]+'#include "av1/common/cdef_gate_audit.h"\n'+s[idx:];p.write_text(s)
    edit('av1/common/thread_common.c','''  if (!row) return;
#if CONFIG_MULTITHREAD
  AV1CdefRowSync *const cdef_row_mt''','''  if (!row) return;
  const uint64_t gate_begin = cdef_gate_now();
#if CONFIG_MULTITHREAD
  AV1CdefRowSync *const cdef_row_mt''')
    edit('av1/common/thread_common.c','''  pthread_mutex_unlock(cdef_row_mt[row - 1].row_mutex_);''','''  pthread_mutex_unlock(cdef_row_mt[row - 1].row_mutex_);
  cdef_row_mt[row].gate_wait_ns = cdef_gate_now() - gate_begin;''')
    edit('av1/common/thread_common.c','''  cdef_sync->cdef_mt_exit = false;
}''','''  cdef_sync->cdef_mt_exit = false;
}''')
    edit('av1/decoder/decodeframe.c','''      if (do_cdef) {
        if (pbi->num_workers > 1) {''','''      if (do_cdef) {
        const uint64_t gate_begin = cdef_gate_now();
        if (pbi->num_workers > 1) {
          for (int r=0; r<cm->cdef_info.allocated_mi_rows; ++r)
            pbi->cdef_sync.cdef_row_mt[r].gate_wait_ns = 0;''')
    edit('av1/decoder/decodeframe.c','''                         av1_cdef_init_fb_row);
        }
      }

      superres_post_decode''','''                         av1_cdef_init_fb_row);
        }
        uint64_t stage_ns = cdef_gate_now() - gate_begin, wait_ns = 0;
        size_t requested=0, usable=0;
        for (int p=0; p<av1_num_planes(cm); ++p) {
          requested += cm->cdef_info.allocated_linebuf_size[p];
          usable += cdef_gate_usable(cm->cdef_info.linebuf[p]);
        }
        if (pbi->num_workers > 1)
          for (int r=0; r<cm->cdef_info.allocated_mi_rows; ++r)
            wait_ns += pbi->cdef_sync.cdef_row_mt[r].gate_wait_ns;
        fprintf(stderr,"{\\"event\\":\\"cdef_frame\\",\\"workers\\":%d,\\"rows\\":%d,\\"requested_bytes\\":%zu,\\"usable_bytes\\":%zu,\\"stage_ns\\":%llu,\\"row_sync_wait_ns\\":%llu,\\"pool_wait_count\\":0}\\n",
                pbi->num_workers,cm->cdef_info.allocated_mi_rows,requested,usable,
                (unsigned long long)stage_ns,(unsigned long long)wait_ns);
      }

      superres_post_decode''')
    if variant!='token': continue
    # Failures use the worker-local longjmp target, outside every mutex.
    edit('av1/common/thread_common.c','''// Hook function for each thread in CDEF multi-threading.''','''static void cdef_gate_fault(AV1CdefSync *sync, int row, int stage) {
  if (cdef_gate_env("CDEF_GATE_FAULT_STAGE", 0) != stage ||
      cdef_gate_env("CDEF_GATE_FAULT_ROW", 1) != row) return;
#if CONFIG_MULTITHREAD
  pthread_mutex_lock(sync->mutex_);
#endif
  int fire = !sync->gate_fault_fired;
  sync->gate_fault_fired = 1;
#if CONFIG_MULTITHREAD
  pthread_mutex_unlock(sync->mutex_);
#endif
  if (fire) {
    fprintf(stderr,"{\\"event\\":\\"fault\\",\\"stage\\":%d,\\"row\\":%d}\\n",stage,row);
    aom_internal_error(sync->cdef_row_mt[row].gate_error, AOM_CODEC_ERROR,
                       "CDEF gate source fault stage %d",stage);
  }
}

// Hook function for each thread in CDEF multi-threading.''')
    edit('av1/common/thread_common.c','''    MACROBLOCKD *xd = cdef_worker->xd;
    av1_cdef_fb_row''','''    cdef_sync->cdef_row_mt[cur_fbr].gate_error = error_info;
    cdef_gate_fault(cdef_sync, cur_fbr, 1);
    MACROBLOCKD *xd = cdef_worker->xd;
    av1_cdef_fb_row''')
    edit('av1/common/thread_common.c','''    cdef_release_boundaries(cdef_sync, cur_fbr, nvfb);''','''    cdef_gate_fault(cdef_sync, cur_fbr, 4);
    cdef_release_boundaries(cdef_sync, cur_fbr, nvfb);
    cdef_gate_fault(cdef_sync, cur_fbr, 5);''')
    edit('av1/common/thread_common.c','''      if (fbr != nvfb - 1)  // if (fbr != 0)  // top line buffer copy''','''      cdef_gate_fault(cdef_sync, fbr, 7);  // Before source copy site.
      if (fbr != nvfb - 1)  // if (fbr != 0)  // top line buffer copy''')
    edit('av1/common/thread_common.c','''      if (fbr != nvfb - 1)  // bottom line buffer copy''','''      cdef_gate_fault(cdef_sync, fbr, 6);  // Partial copy: top done, bottom absent.
      if (fbr != nvfb - 1)  // bottom line buffer copy''')
    edit('av1/common/thread_common.c','''  cdef_row_mt_sync_write(cdef_sync, fbr);
  cdef_row_mt_sync_read(cdef_sync, fbr);''','''  cdef_gate_fault(cdef_sync, fbr, 2);
  cdef_row_mt_sync_write(cdef_sync, fbr);
  cdef_gate_fault(cdef_sync, fbr, 3);
  cdef_row_mt_sync_read(cdef_sync, fbr);''')
    edit('av1/common/alloccommon.c','''    if (linebuf[plane] == NULL)
      CHECK_MEM_ERROR(cm, linebuf[plane],
                      aom_malloc(cdef_info->allocated_linebuf_size[plane]));''','''    if (linebuf[plane] == NULL)
      CHECK_MEM_ERROR(cm, linebuf[plane],
                      cdef_gate_env("CDEF_GATE_ALLOC_PLANE", -1) == plane ? NULL :
                      aom_malloc(cdef_info->allocated_linebuf_size[plane]));''')
    edit('av1/common/alloccommon.c','''                    aom_calloc(strips, sizeof(*cdef_sync->boundary_owner)));''','''                    cdef_gate_env("CDEF_GATE_ALLOC_OWNER", 0) ? NULL :
                    aom_calloc(strips, sizeof(*cdef_sync->boundary_owner)));''')
    edit('av1/common/alloccommon.c','''  aom_free(cdef_sync->boundary_owner);
  cdef_sync->boundary_owner = NULL;
  cdef_sync->top_slots = cdef_sync->bottom_slots = 0;''','''  aom_free(cdef_sync->boundary_owner);
  cdef_sync->boundary_owner = NULL;
  cdef_sync->top_slots = cdef_sync->bottom_slots = 0;
  fprintf(stderr,"{\\"event\\":\\"cdef_pool_freed\\"}\\n");''')
