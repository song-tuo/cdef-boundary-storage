# Details retained outside the concise manuscript

This editorial revision relocates details from the preceding manuscript; it creates no new scientific result. The complete records remain in the immutable evidence archive identified by EVIDENCE_BASE.json. EVIDENCE_MAP.csv maps this revision's claims to those records.

## Implementation anchors and lifecycle

In thread_common.c, get_cdef_row_next_job reserves slots, av1_cdef_init_fb_row_mt copies and synchronizes, and cdef_release_boundaries reclaims them. Exhaustion raises an invariant error, not a capacity wait. Workers retain ownership until release; the worker longjmp/wakeup path joins workers before resetting ownership for the next frame. Resizing and destruction preserve the existing allocation lifecycle. SOURCE_ANCHORS.csv and CONTRACT_SOURCE_EVIDENCE.md in the evidence archive provide the full mapping.

The one-row MT case has zero logical boundary strips and an unused allocation sentinel. The abstract row-job theorem includes one worker; the actual libaom W=1 serial ping-pong implementation is a compatibility path.

## Validation counts and exclusions

The original Release check has 180 configurations and 540 records across the uncorrected row-indexed, sample-size-corrected row-indexed, and owner-pool builds. Debug, ASan+UBSan and TSan each have 180 matching configurations. Each sanitizer fault suite contains 156 fault/control runs plus 156 subsequent clean decodes, with 99 same-instance recovery cases. The selected upstream conformance configurations execute 3899 test IDs each. Native leak checks contain 36 clean cases and a successful positive probe.

Runtime SVE/SVE2, macOS LeakSanitizer and three disabled resize speed cases are outside the executed coverage. They remain excluded, not counted as passes. H1's independent hybrid checks retain all collisions/exhaustion/lifecycle/error records. Across three implementations, 432 clean/instrumented configurations produce 2592 matching output and row-copy records. Nine fixed encodings from three official clips produce 81 runs across 27 cases. These real-content runs check output and copies; they are not new natural-video timing evidence.

## Allocation and timing

RESOURCE_ACCOUNTING.md retains requested/usable bytes, owner/index metadata, worker structures, padding and historical process-memory endpoints. The 4K/eight-worker usable pixel allocations are 2097152 and 524288 bytes, expressed as 2048 and 512 KiB in the concise paper. Some accounting categories overlap and must not be added indiscriminately. The historical process RSS includes harness and other decoder allocations and is not a matched whole-decoder memory percentage.

H1 retains 216 independent blocks, three implementations per block and 648 process measurements. The original summaries used 50000 whole-block bootstrap draws per cell. Owner-pool/reference remains secondary/descriptive. The primary hybrid/reference result remains six passes and twelve inconclusive cells at the fixed 1.02 margin. H1's decision remains KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT. No new samples, bootstrap draws or alternative analysis were run.

## Addressing alternatives

The manuscript explains the difference between preserving existing copy-ready interleavings and adding a free-slot dependency. Halide's official async tutorial, example using fold_storage(c, 2), explicitly blocks production until storage is available and releases space after consumption. Its ring_buffer(2) example follows the same structure. This is a cited conceptual distinction, not a newly implemented libaom baseline or a measured slowdown claim.

Primary source checked on 2026-10-02: https://halide-lang.org/docs/tutorial/lesson_24_async.html (fold_storage example and ring_buffer example). The theorem, all proofs and Proposition 1 are unchanged. The simplified figure marks copy completion C_i and release completion Q_i; reservations before copy remain included in the proof.
