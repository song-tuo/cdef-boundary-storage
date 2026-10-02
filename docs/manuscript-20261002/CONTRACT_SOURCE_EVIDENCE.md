# Execution contract -> source -> preserved evidence

Line numbers below refer to the copied owner-pool source at `records/CDEF_full_source_gate/src/token/`, not the upstream unmodified source. `SOURCE_ANCHORS.csv` records file SHA-256 values and anchor lines. The `baseline_to_type_fix.patch` and `type_fix_to_token.patch` files separate sample-size correction from ownership reuse. In H1 the same owner-pool implementation is named `dual_token`.

| Contract or paper step | Source anchor | Existing evidence and interpretation |
|---|---|---|
| Each worker holds one row through release, then requests the next | `av1/common/thread_common.c`, `cdef_sb_row_worker_hook`, lines 1131-1189 | H1 audit events `dispatch`, `filter_done`, `release`; parser `scripts/checks.py`. The theorem's set A includes jobs whose release is incomplete. |
| Monotone row issue and address reservation under the existing mutex | Same file, `get_cdef_row_next_job`, lines 1091-1124 | H1 `semantic_matrix.csv`, per-case `command_log`, audit stderr. Nonfinal row i reserves T(i+1) with owner i+1 and B(i) with owner i. Incoming T(i) was reserved by the prior dispatch. |
| Slot acquisition never adds a capacity wait | Same file, `cdef_take_boundary`, lines 1054-1063 | First-free scan returns -1 on invariant failure. The worker hook raises `CDEF token exhaustion`; records retain exhaustion flags and raw errors. The capacity theorem applies to normal execution. |
| Copy before publish, predecessor wait before filter | Same file, `av1_cdef_init_fb_row_mt`, lines 1217-1279; `cdef_row_mt_sync_write/read`, lines 175-203; `av1/common/cdef.c`, `av1_cdef_fb_row`, lines 426-465 | Raw H1 audit stderr records copy/signal/wait events; `scripts/checks.py` checks per-row order and predecessor readiness. It canonicalizes copy tuples for hash comparison rather than demanding identical cross-worker wall-clock interleaving. |
| Consumer releases incoming top and own bottom; producer keeps outgoing top | `thread_common.c`, `cdef_release_boundaries`, lines 1065-1087; hook call after `av1_cdef_fb_row` | Owner assertions and H1 shadow instrumentation check invalid owners, collisions and exhaustion. The normal-path pseudocode is an exposition of these functions, not a replacement implementation. |
| Worker failure wakes dependents, then cleanup/reset follows joined workers | Same file, setjmp branch in `cdef_sb_row_worker_hook`; `set_cdef_init_fb_row_done`; `av1_cdef_frame_mt`, lines 1288-1321 | Full-source `fault_injection*.json`, `same_instance_recovery*.json`; H1 `fault_recovery.csv`, raw stderr and result records. A longjmp can bypass normal per-row release. Ownership resets after worker join; no per-row transactional rollback is asserted. |
| Exact MT capacity, separate serial path, resize/free lifecycle | `av1/common/alloccommon.c`, `av1_alloc_cdef_buffers`, lines 195 onward (capacity lines 219-244, owner allocation 300-302); `av1_free_cdef_buffers`, lines 122 onward | H1 `allocation_accounting.csv`, `safety_matrix.csv`, sequences and recovery logs. W=1 is the retained serial compatibility control; one-row MT uses an unused allocation sentinel outside logical strip count. |
| Tightness and unsafe static addressing | Manuscript proof and figure; full-source `results/ownership_schedule_model.json`; H1 `results/theory_check.json` | Analytical and model witnesses are separate from observed decoder traces. See `WITNESS_AND_MEASUREMENT_SCOPE.md`. |

## One traceable recorded case

Use command name `sem_audit_s_w2_r19_10_420_c1_w2_m1_dual_token` in `records/CDEF_H1/COMMANDS.json`. The corresponding files under `logs/` retain the exact command, result, stdout and stderr. The archived command invokes the existing audit harness with input `s_w2_r19_10_420_c1.ivf`, W=2 and row-MT enabled. Its immutable input identity is in `inputs/generated_manifest.json`; its prescribed configuration is in `protocol/semantic_inputs.json`; the compared result is in `semantic_matrix.csv` and `results/semantic_cases/`.

This example is an index into a previously executed case. It is not a new run or a decoder trace forced to attain the theorem's maximum. All other cases remain in the bundle, including inactive CDEF paths and failed attempts.

## Copy audit semantics

The H1 parser groups copies by frame, retains `(row, plane, kind, samples, hash)`, sorts those tuples, and hashes their canonical serialization. Per-row event order and predecessor readiness are checked separately. Matching this copy audit establishes matching copied data at the intended rows and planes. It does not mean that independent workers produced an identical global event ordering.

Release output comparisons use frame counts and visible-plane hashes. Sanitizer instrumentation and accounting instrumentation are separate builds; timing records come from the clean Release builds. The copied protocols and seals identify these roles.
