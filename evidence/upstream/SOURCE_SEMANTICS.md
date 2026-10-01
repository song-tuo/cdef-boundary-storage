# Current upstream CDEF semantics

The official v3.15.1 release and current main snapshot have identical bytes in the five audited files. Both still use row-indexed boundary storage and the pointer-width sizeof expression. The exact source identities, tree completeness checks, and line locations are recorded locally; this establishes persistence at retrieval time, not at a future submission date.

## Source contract in normal execution

| Event | v3.15.1 and main baseline location | Observation |
|---|---|---|
| Boundary element type | av1/common/av1_common_int.h:207 | `uint16_t *linebuf[MAX_MB_PLANE]`; one dereference is a pointer, two dereferences are a uint16_t sample. |
| Requested storage | av1/common/alloccommon.c:209–226 | Serial uses num_bufs=3; multithreading uses frame-row count R. The allocation multiplies `sizeof(*cdef_info->linebuf)` by 2R strips' dimensions. |
| Ordered row dispatch | av1/common/thread_common.c:1047–1072 | Existing job mutex protects fbr read/increment. |
| Snapshot copy | av1/common/thread_common.c:1190–1211 | Row r copies its last two rows for row r+1's top boundary and next row's first two rows for its own bottom boundary. These are pre-filter snapshots. |
| Copy-ready signal | av1/common/thread_common.c:1221; function at193–205 | After the copy loop for all planes, signal the row condition and set is_row_done=1 under its mutex. |
| Predecessor-ready wait | av1/common/thread_common.c:1222; function at177–191 | Wait for row r-1's is_row_done, then reset it. No predecessor filter-return check occurs here. |
| Filtering starts afterward | av1/common/cdef.c:439–456 | Row initializer completes first; then the function traverses columns and filters blocks. |
| Boundary reads span columns | av1/common/cdef.c:192–234 | Each block copies required top/bottom boundary fragments into its local scratch. Whole strips stay available through the row call. |
| Filter return | av1/common/thread_common.c:1116–1118; cdef.c:458 | av1_cdef_fb_row returns after its column traversal. A worker can then request another row. |
| Token retention/release | av1/common/thread_common.c in token:1067–1089,1164–1174 | Incoming top and own bottom release only after av1_cdef_fb_row returns. Outgoing top is released by its consumer, not its producer. |

**Inference from this call order:** on the successful path, ready means copies are complete; it does not imply filtering is complete. A consumer can keep using its incoming top while other workers advance.

There is a separate error-unblocking path: thread_common.c:1098–1107 signals all rows to avoid indefinite waits when a worker aborts. That artificial signal is followed by the exit check at cdef.c:441–446. It is not a successful-copy guarantee and is outside a successful-execution capacity witness.

## Why preserve the existing copy contract?

Replacing the saved incoming top with a consumer-side copy directly from the frame changes the synchronization requirement. After its own initialization and predecessor-ready wait, the preceding row may already overwrite those pixels by filtering in place; no wait for its successor's private copy exists. A correct direct-frame alternative must add a rendezvous before predecessor filtering, or move the copy earlier. Copying instead from the producer's saved snapshot avoids that race but adds a copy into private storage and changes when/where ownership transfers. These are legitimate alternative contracts, whose capacity and performance require separate analysis. The present token patch keeps the original source-copy positions and waits, then maps retained snapshots to reusable slots.

## Conditional row-engine consequence

The liveness argument depends on issue order, at most W active row consumers, the same pre-filter copy ordering, and indivisible whole-strip retention through consumer return. Any software or hardware row engine implementation satisfying those premises has the same retained-strip capacity problem. A software allocation measurement does not establish physical SRAM area, power, or energy. This is a conditional scheduling/storage consequence, not an implementation or synthesis result.
