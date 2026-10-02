# Patch ledger

All three clean implementations share the same frozen v3.12.1 source lineage. They retain the previous Debian source package's eight non-CDEF packaging modifications (system libyuv/webm integration and documentation). Those branches are disabled by CONFIG_LIBYUV=0, CONFIG_WEBM_IO=0, ENABLE_DOCS=OFF. `official_to_shared_packaging.patch` records every shared difference from the official archive; all 1,347 official files are present. Source identity is not claimed for the entire patched tree. The relevant upstream CDEF originals are separately Git-blob verified in Stage 0.

- `baseline_to_type_fix.patch`: only the existing CDEF sample-size sizeof correction relative to that shared base.
- `type_fix_to_token.patch`: the exact pre-existing dual-token implementation. Old source and patch hashes were verified; old correctness or timing results were not reused as hybrid evidence.
- `dual_token_to_hybrid.patch`: three CDEF common files. Top-only owner allocation; persistent worker bottom index or direct row index; remove bottom free scan/release state. No CDEF arithmetic, DSP change, new copy site, new condition variable or changed issue order.
- `*_to_audit.patch`: separately instrumented source trees for copy/order/ownership/allocation events and explicit fault hooks. Shadow active-row state belongs only to diagnostics.
- `*_to_account.patch`: allocation-only observers, with unchanged production structure layouts and malloc_size backing-block measurements.

Before the first decoder experiment, source preparation first hit an ambiguous text anchor and was corrected; a later observer build exposed a missing audit-header include in serial cdef.c. Failed command logs and the prior source-preparation script are preserved. Atomic placement of the diagnostic active-row release was completed before execution. No scientific outcome had been observed at those repairs. Logs 020/021 establish sealing before the first decoder matrix.

The source trees, inputs, test harnesses and core binaries were sealed in protocol/IMPLEMENTATION_SEAL.json. Subsequent scripts only dispatch frozen executions or derive tables; no production, audit, input, threshold, worker-count or timing-schedule changes followed scientific results. The separate FPMT build is sealed before its tests. The timing runner and schedule are sealed before timing. The after-run source/implementation recheck and read-only prior-source checks are supplied.

Metadata is not hidden: each row still carries top_slot and bottom_slot indices. Hybrid removes the bottom owner array, not these row addresses. The worker bottom_slot adds 4 logical bytes per worker and 8 bytes per worker in this ABI's structure layout. Accounting reports that padding and the allocator's backing allocation separately.
