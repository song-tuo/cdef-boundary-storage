from pathlib import Path
import shutil,hashlib,json,difflib
ROOT=Path(__file__).resolve().parents[1]; OLD=ROOT.parent/'CDEF_full_source_gate'
files=['av1/common/thread_common.c','av1/common/thread_common.h','av1/common/alloccommon.c']
def change(s,a,b,n=1):
 assert s.count(a)==n,(a[:100],s.count(a));return s.replace(a,b)
for variant in ['token','ring']:
 dest=ROOT/'src'/variant;assert not dest.exists();shutil.copytree(OLD/'src/token',dest)
 h=(dest/files[1]).read_text(); c=(dest/files[0]).read_text()
 h=change(h,'  int bottom_slot;\n} AV1CdefRowSync;', '''  int bottom_slot;
#ifdef CDEF_POOL_DIAGNOSTICS
  int capacity_wait_seen;
#endif
} AV1CdefRowSync;''')
 h=change(h,'  int bottom_slots;\n  // Flag', '''  int bottom_slots;
#ifdef CDEF_POOL_DIAGNOSTICS
  uint64_t pool_wait_ns;
  unsigned pool_wait_calls, pool_wait_rows, pool_dispatch_rows;
  int diag_hold_row, diag_hold_ms, diag_fault_row;
#endif
  // Flag''')
 helper='''
#ifdef CDEF_POOL_DIAGNOSTICS
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <errno.h>
static uint64_t cdef_pool_now(void) {
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return (uint64_t)t.tv_sec * 1000000000ULL + t.tv_nsec;
}
static int cdef_pool_env(const char *key, int fallback) {
  const char *s = getenv(key);
  return s ? atoi(s) : fallback;
}
static void cdef_pool_hold(int ms) {
  struct timespec t = { ms / 1000, (ms % 1000) * 1000000L };
  while (nanosleep(&t, &t) != 0 && errno == EINTR) {}
}
#endif

'''
 c=change(c,'// Initializes cdef_sync parameters.',helper+'// Initializes cdef_sync parameters.')
 c=change(c,'    cdef_release_boundaries(cdef_sync, cur_fbr, nvfb);', '''#ifdef CDEF_POOL_DIAGNOSTICS
    if (cur_fbr == cdef_sync->diag_hold_row && cdef_sync->diag_hold_ms > 0)
      cdef_pool_hold(cdef_sync->diag_hold_ms);
    if (cur_fbr == cdef_sync->diag_fault_row)
      aom_internal_error(error_info, AOM_CODEC_ERROR, "CDEF pool test fault");
#endif
    cdef_release_boundaries(cdef_sync, cur_fbr, nvfb);''')
 c=change(c,'  reset_cdef_job_info(cdef_sync);\n  prepare_cdef_frame_workers', '''#ifdef CDEF_POOL_DIAGNOSTICS
  cdef_sync->pool_wait_ns = 0;
  cdef_sync->pool_wait_calls = cdef_sync->pool_wait_rows = 0;
  cdef_sync->pool_dispatch_rows = 0;
  cdef_sync->diag_hold_row = cdef_pool_env("CDEF_POOL_HOLD_ROW", -1);
  cdef_sync->diag_hold_ms = cdef_pool_env("CDEF_POOL_HOLD_MS", 0);
  cdef_sync->diag_fault_row = cdef_pool_env("CDEF_POOL_FAULT_ROW", -1);
  for (int i = 0; i < rows; ++i) cdef_sync->cdef_row_mt[i].capacity_wait_seen = 0;
#endif
  reset_cdef_job_info(cdef_sync);
  prepare_cdef_frame_workers''')
 report='''#ifdef CDEF_POOL_DIAGNOSTICS
  size_t bytes = 0;
  for (int p = 0; p < av1_num_planes(cm); ++p)
    bytes += cm->cdef_info.allocated_linebuf_size[p];
  fprintf(stderr, "{\\"event\\":\\"cdef_pool_diag\\",\\"variant\\":\\"VARIANT\\","
          "\\"workers\\":%d,\\"rows\\":%d,\\"top_slots\\":%d,\\"bottom_slots\\":%d,"
          "\\"requested_bytes\\":%zu,\\"dispatch_rows\\":%u,\\"wait_rows\\":%u,"
          "\\"wait_calls\\":%u,\\"worker_wait_ns\\":%llu}\\n",
          num_workers, rows, cdef_sync->top_slots, cdef_sync->bottom_slots,
          bytes, cdef_sync->pool_dispatch_rows, cdef_sync->pool_wait_rows,
          cdef_sync->pool_wait_calls, (unsigned long long)cdef_sync->pool_wait_ns);
#endif
'''.replace('VARIANT',variant)
 c=change(c,'  sync_cdef_workers(workers, cm, num_workers);\n#ifndef NDEBUG','  sync_cdef_workers(workers, cm, num_workers);\n'+report+'#ifndef NDEBUG')
 if variant=='token':
  c=change(c,'    update_cdef_row_next_job_info(cdef_sync, nvfb);', '''#ifdef CDEF_POOL_DIAGNOSTICS
    ++cdef_sync->pool_dispatch_rows;
#endif
    update_cdef_row_next_job_info(cdef_sync, nvfb);''')
 else:
  # These fields belong only to CDEF's dispatcher (not restoration/loopfilter).
  h=change(h,'  // Mutex lock used while dispatching jobs.\n  pthread_mutex_t *mutex_;', '''  // Mutex lock used while dispatching jobs.
  pthread_mutex_t *mutex_;
  pthread_cond_t *boundary_cond_;
  unsigned boundary_waiters;''')
  c=change(c,'    if (cdef_sync->mutex_) pthread_mutex_init(cdef_sync->mutex_, NULL);\n  }', '''    if (cdef_sync->mutex_) pthread_mutex_init(cdef_sync->mutex_, NULL);
  }
  if (cdef_sync->boundary_cond_ == NULL) {
    CHECK_MEM_ERROR(cm, cdef_sync->boundary_cond_,
                    aom_malloc(sizeof(*cdef_sync->boundary_cond_)));
    pthread_cond_init(cdef_sync->boundary_cond_, NULL);
  }''')
  c=change(c,'  if (cdef_sync->mutex_ != NULL) {\n    pthread_mutex_destroy', '''  if (cdef_sync->boundary_cond_ != NULL) {
    pthread_cond_destroy(cdef_sync->boundary_cond_);
    aom_free(cdef_sync->boundary_cond_);
    cdef_sync->boundary_cond_ = NULL;
  }
  if (cdef_sync->mutex_ != NULL) {
    pthread_mutex_destroy''')
  start=c.index('// Called only with the existing job mutex held.')
  end=c.index('static void cdef_release_boundaries',start)
  c=c[:start]+c[end:]
  c=change(c,'  pthread_mutex_unlock(sync->mutex_);\n#endif\n}', '''  if (sync->boundary_waiters) pthread_cond_broadcast(sync->boundary_cond_);
  pthread_mutex_unlock(sync->mutex_);
#endif
}''')
  start=c.index('// Checks if a job is available. Returns -1')
  end=c.index('static void set_cdef_init_fb_row_done',start)
  c=c[:start]+'''// Fixed identity mapping with ordered reservation. A blocked dispatcher
// releases the mutex so existing consumers can finish and return their slots.
static inline int get_cdef_row_next_job(AV1CdefSync *const cdef_sync,
                                        volatile int *cur_fbr, const int nvfb) {
#if CONFIG_MULTITHREAD
  pthread_mutex_lock(cdef_sync->mutex_);
#endif
  int do_next_row = 0;
  while (!cdef_sync->cdef_mt_exit && !cdef_sync->end_of_frame) {
    const int row = cdef_sync->fbr;
    if (row < nvfb - 1) {
      const int top = row % cdef_sync->top_slots;
      const int bottom = row % cdef_sync->bottom_slots;
      if (cdef_sync->boundary_owner[top] != -1 ||
          cdef_sync->boundary_owner[cdef_sync->top_slots + bottom] != -1) {
#if CONFIG_MULTITHREAD
#ifdef CDEF_POOL_DIAGNOSTICS
        if (!cdef_sync->cdef_row_mt[row].capacity_wait_seen) {
          cdef_sync->cdef_row_mt[row].capacity_wait_seen = 1;
          ++cdef_sync->pool_wait_rows;
        }
        ++cdef_sync->pool_wait_calls;
        const uint64_t begin = cdef_pool_now();
#endif
        ++cdef_sync->boundary_waiters;
        pthread_cond_wait(cdef_sync->boundary_cond_, cdef_sync->mutex_);
        --cdef_sync->boundary_waiters;
#ifdef CDEF_POOL_DIAGNOSTICS
        cdef_sync->pool_wait_ns += cdef_pool_now() - begin;
#endif
        continue;
#else
        do_next_row = -1;
        break;
#endif
      }
      cdef_sync->boundary_owner[top] = row + 1;
      cdef_sync->boundary_owner[cdef_sync->top_slots + bottom] = row;
      cdef_sync->cdef_row_mt[row + 1].top_slot = top;
      cdef_sync->cdef_row_mt[row].bottom_slot = bottom;
    }
    *cur_fbr = row;
    do_next_row = 1;
#ifdef CDEF_POOL_DIAGNOSTICS
    ++cdef_sync->pool_dispatch_rows;
#endif
    update_cdef_row_next_job_info(cdef_sync, nvfb);
    break;
  }
#if CONFIG_MULTITHREAD
  pthread_mutex_unlock(cdef_sync->mutex_);
#endif
  return do_next_row;
}

'''+c[end:]
  c=change(c,'    cdef_sync->cdef_mt_exit = true;\n    pthread_mutex_unlock(job_mutex_);', '''    cdef_sync->cdef_mt_exit = true;
    pthread_cond_broadcast(cdef_sync->boundary_cond_);
    pthread_mutex_unlock(job_mutex_);''')
  c=change(c,'  const int rows = cm->cdef_info.allocated_mi_rows;', '''#if CONFIG_MULTITHREAD
  assert(cdef_sync->boundary_waiters == 0);
#endif
  const int rows = cm->cdef_info.allocated_mi_rows;''')
 (dest/files[0]).write_text(c);(dest/files[1]).write_text(h)
 for f in files:
  original=(OLD/'src/token'/f).read_text();new=(dest/f).read_text()
  if original!=new:
   path=ROOT/'patches'/f'token_to_{variant}_with_optional_diagnostics.patch'
   with path.open('a') as out:out.writelines(difflib.unified_diff(original.splitlines(True),new.splitlines(True),fromfile='a/'+f,tofile='b/'+f))
shutil.copy2(OLD/'scripts/ivf_gate.c',ROOT/'scripts/ivf_gate.c')
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for v in ['token','ring'] for p in (ROOT/'src'/v).rglob('*') if p.is_file()}
(ROOT/'protocol/source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared separate full token/ring source trees',len(manifest))
