"""Reproduce source-local token changes from the type-correct Debian tree."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src/token'

def change(name, old, new):
    p = SRC / name
    s = p.read_text()
    assert s.count(old) == 1, (name, old[:80], s.count(old))
    p.write_text(s.replace(old, new))

change('av1/common/thread_common.h', '  int is_row_done;\n} AV1CdefRowSync;', '''  int is_row_done;
  // Assigned under the job mutex before dispatch; immutable for this frame.
  int top_slot;
  int bottom_slot;
} AV1CdefRowSync;''')
change('av1/common/thread_common.h', '  AV1CdefRowSync *cdef_row_mt;', '''  AV1CdefRowSync *cdef_row_mt;
  // Pool entries contain the consuming row, or -1 when free. The existing
  // job mutex protects ownership; pixel copies retain the row-sync contract.
  int *boundary_owner;
  int top_slots;
  int bottom_slots;''')
change('av1/common/alloccommon.c', '  free_cdef_row_sync(&cdef_sync->cdef_row_mt, num_mi_rows);', '''  free_cdef_row_sync(&cdef_sync->cdef_row_mt, num_mi_rows);
  aom_free(cdef_sync->boundary_owner);
  cdef_sync->boundary_owner = NULL;
  cdef_sync->top_slots = cdef_sync->bottom_slots = 0;''')
change('av1/common/alloccommon.c', '''  if (is_cdef_enabled) {
    // Calculate src buffer size''', '''  const int top_slots = num_workers > 1 ? AOMMIN(num_mi_rows - 1, num_workers + 1) : 0;
  const int bottom_slots = num_workers > 1 ? AOMMIN(num_mi_rows - 1, num_workers) : 0;
  const size_t strips = num_workers > 1 ? (size_t)top_slots + bottom_slots
                                      : (size_t)num_bufs * 2;
  if (cdef_sync->top_slots != top_slots || cdef_sync->bottom_slots != bottom_slots) {
    aom_free(cdef_sync->boundary_owner);
    cdef_sync->boundary_owner = NULL;
  }
  cdef_sync->top_slots = top_slots;
  cdef_sync->bottom_slots = bottom_slots;

  if (is_cdef_enabled) {
    // Calculate src buffer size''')
change('av1/common/alloccommon.c', '''      new_linebuf_size[plane] = sizeof(**cdef_info->linebuf) * num_bufs *
                                (CDEF_VBORDER << 1) * (luma_stride >> shift);''', '''      const size_t strip_bytes =
          sizeof(**cdef_info->linebuf) * CDEF_VBORDER * (size_t)(luma_stride >> shift);
      if (strips && strip_bytes > SIZE_MAX / strips)
        aom_internal_error(cm->error, AOM_CODEC_MEM_ERROR, "CDEF boundary size overflow");
      // One unused sample keeps the zero-boundary, one-row case non-null.
      new_linebuf_size[plane] = AOMMAX(sizeof(uint16_t), strips * strip_bytes);''')
change('av1/common/alloccommon.c', '''  if (num_workers < 2) return;

  if (init_worker) {''', '''  if (num_workers < 2) return;

  if (strips && cdef_sync->boundary_owner == NULL)
    CHECK_MEM_ERROR(cm, cdef_sync->boundary_owner,
                    aom_calloc(strips, sizeof(*cdef_sync->boundary_owner)));

  if (init_worker) {''')

change('av1/common/thread_common.c', '''// Checks if a job is available. If job is available,
// populates next job information and returns 1, else returns 0.''', '''// Called only with the existing job mutex held. Exhaustion is an invariant
// failure, never a reason to wait or serialize otherwise runnable rows.
static int cdef_take_boundary(int *owners, int count, int row) {
  for (int i = 0; i < count; ++i) {
    if (owners[i] == -1) {
      owners[i] = row;
      return i;
    }
  }
  return -1;
}

static void cdef_release_boundaries(AV1CdefSync *sync, int row, int rows) {
#if CONFIG_MULTITHREAD
  pthread_mutex_lock(sync->mutex_);
#endif
  // Incoming top is produced by row-1 and consumed through the END of this
  // row's filter. Own bottom has the same consumer lifetime. Outgoing top
  // belongs to row+1 and is deliberately not released by its producer.
  if (row > 0) {
    const int slot = sync->cdef_row_mt[row].top_slot;
    assert(slot >= 0 && slot < sync->top_slots);
    assert(sync->boundary_owner[slot] == row);
    sync->boundary_owner[slot] = -1;
  }
  if (row < rows - 1) {
    const int slot = sync->cdef_row_mt[row].bottom_slot;
    assert(slot >= 0 && slot < sync->bottom_slots);
    assert(sync->boundary_owner[sync->top_slots + slot] == row);
    sync->boundary_owner[sync->top_slots + slot] = -1;
  }
#if CONFIG_MULTITHREAD
  pthread_mutex_unlock(sync->mutex_);
#endif
}

// Checks if a job is available. Returns -1 on an ownership invariant error.
// There is no token-pool condition variable and no token-capacity wait.''')
change('av1/common/thread_common.c', '''    *cur_fbr = cdef_sync->fbr;
    update_cdef_row_next_job_info(cdef_sync, nvfb);''', '''    *cur_fbr = cdef_sync->fbr;
    // Dispatch is ordered. The previous dispatch has already reserved our
    // incoming top. Reserve the chain tail and our bottom before issuing.
    if (*cur_fbr < nvfb - 1) {
      const int top = cdef_take_boundary(cdef_sync->boundary_owner,
                                         cdef_sync->top_slots, *cur_fbr + 1);
      const int bottom = cdef_take_boundary(
          cdef_sync->boundary_owner + cdef_sync->top_slots,
          cdef_sync->bottom_slots, *cur_fbr);
      if (top < 0 || bottom < 0) {
        cdef_sync->cdef_mt_exit = true;
        do_next_row = -1;
      } else {
        cdef_sync->cdef_row_mt[*cur_fbr + 1].top_slot = top;
        cdef_sync->cdef_row_mt[*cur_fbr].bottom_slot = bottom;
      }
    }
    update_cdef_row_next_job_info(cdef_sync, nvfb);''')
change('av1/common/thread_common.c', '''  while (get_cdef_row_next_job(cdef_sync, &cur_fbr, nvfb)) {
    MACROBLOCKD *xd = cdef_worker->xd;''', '''  int job_status;
  while ((job_status = get_cdef_row_next_job(cdef_sync, &cur_fbr, nvfb))) {
    if (job_status < 0)
      aom_internal_error(error_info, AOM_CODEC_ERROR, "CDEF token exhaustion");
    MACROBLOCKD *xd = cdef_worker->xd;''')
change('av1/common/thread_common.c', '''                    cdef_worker->cdef_init_fb_row_fn, cdef_sync, error_info);
    if (cdef_worker->do_extend_border) {''', '''                    cdef_worker->cdef_init_fb_row_fn, cdef_sync, error_info);
    cdef_release_boundaries(cdef_sync, cur_fbr, nvfb);
    if (cdef_worker->do_extend_border) {''')
change('av1/common/thread_common.c', '''    uint16_t *bot_linebuf = &linebuf[plane][nvfb * CDEF_VBORDER * stride];''', '''    const size_t strip = (size_t)CDEF_VBORDER * stride;
    uint16_t *bot_linebuf = top_linebuf + cdef_sync->top_slots * strip;
    const int incoming = fbr > 0 ? cdef_sync->cdef_row_mt[fbr].top_slot : 0;
    const int outgoing = fbr < nvfb - 1 ? cdef_sync->cdef_row_mt[fbr + 1].top_slot : 0;
    const int bottom = fbr < nvfb - 1 ? cdef_sync->cdef_row_mt[fbr].bottom_slot : 0;''')
change('av1/common/thread_common.c', '&top_linebuf[(fbr + 1) * CDEF_VBORDER * stride]', '&top_linebuf[outgoing * strip]')
change('av1/common/thread_common.c', '&bot_linebuf[fbr * CDEF_VBORDER * stride]', '&bot_linebuf[bottom * strip]')
change('av1/common/thread_common.c', '''    fb_info->top_linebuf[plane] = &linebuf[plane][fbr * CDEF_VBORDER * stride];
    fb_info->bot_linebuf[plane] =
        &linebuf[plane]
                [nvfb * CDEF_VBORDER * stride + (fbr * CDEF_VBORDER * stride)];''', '''    fb_info->top_linebuf[plane] = top_linebuf + incoming * strip;
    fb_info->bot_linebuf[plane] = bot_linebuf + bottom * strip;''')
change('av1/common/thread_common.c', '''  reset_cdef_job_info(cdef_sync);
  prepare_cdef_frame_workers''', '''  // All preceding workers have joined. Reclaim abandoned ownership after
  // an error as well as normal frame completion; destruction frees the same
  // backing allocations regardless of the ownership state at longjmp.
  const int rows = cm->cdef_info.allocated_mi_rows;
  for (int i = 0; i < cdef_sync->top_slots + cdef_sync->bottom_slots; ++i)
    cdef_sync->boundary_owner[i] = -1;
  for (int i = 0; i < rows; ++i) {
    cdef_sync->cdef_row_mt[i].top_slot = -1;
    cdef_sync->cdef_row_mt[i].bottom_slot = -1;
    cdef_sync->cdef_row_mt[i].is_row_done = 0;
  }
  reset_cdef_job_info(cdef_sync);
  prepare_cdef_frame_workers''')
change('av1/common/thread_common.c', '''  sync_cdef_workers(workers, cm, num_workers);
}''', '''  sync_cdef_workers(workers, cm, num_workers);
#ifndef NDEBUG
  for (int i = 0; i < cdef_sync->top_slots + cdef_sync->bottom_slots; ++i)
    assert(cdef_sync->boundary_owner[i] == -1);
#endif
}''')
