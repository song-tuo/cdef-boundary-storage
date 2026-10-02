# CDEF-H1 hybrid design

The independent type_fix, dual_token and hybrid source trees start from the same verified v3.12.1 source lineage. type_fix retains only the sample-size sizeof correction. dual_token is a byte-identical copy of the previously validated source implementation, rebuilt here; its historical test outcomes are not inherited by hybrid.

Hybrid changes only the lifetime-to-address realization in av1/common/{alloccommon.c,thread_common.c,thread_common.h}. The top-only owner array has min(R-1,W+1) integers. The combined pixel allocation still has top+bottom strips. Its bottom segment has min(R-1,W) slots. prepare_cdef_frame_workers sets a worker-local slot index i when R-1>=W, or -1 to select direct row indexing otherwise. Ordered dispatch writes the selected index into the existing per-row bottom_slot field. This per-row index is retained and explicitly charged as metadata; it is not a bottom owner array. Bottom release has no state mutation, free-list operation or scan. Each worker finishes a row before its next dispatch.

No new mutex, condition variable, barrier or capacity wait is introduced. CDEF arithmetic, DSP source and the two boundary copy sites are untouched; only their address selection differs from type_fix, as in the existing dual-token patch. The same worker error path broadcasts readiness and joins workers before ownership is reset or storage destroyed. Encoder FPMT worker arrays are tested independently because worker state is shared by that path.

Audit builds are separate copies. They log canonical per-row/plane copy hashes, raw dispatch/signal/wait/filter/release order, allocation/free events and active-row slot checks. Allocation-only builds omit the added audit fields and measure the real implementation structures. Primary timing uses clean Release builds with neither class of audit instrumentation.

The existing single-worker serial path is unchanged and tested for exact compatibility. No claim is made that its legacy allocation implements the new row-MT capacity formula.
