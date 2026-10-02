# Witnesses and measured endpoints

## Three distinct kinds of support

1. **Analytical construction.** The manuscript's proof constructs a legal schedule attaining both component maxima together. Figure 1(B) depicts a legal W=2, R=5 copied-strip state. Neither is presented as a recorded decoder schedule.
2. **Preserved finite-state checks.** The full-source `ownership_schedule_model.json` and H1 `theory_check.json` store the earlier enumeration results and witnesses. Their scripts model dispatch, readiness and release. Reserved slots and completed copies are distinct events: a peak in a reservation model alone is not a measured copied-strip peak. No enumerator was rerun for this revision.
3. **Observed implementation behavior.** The H1 audit stderr and semantic/safety tables record actual instrumented decoder execution, copied data, owner checks, lifecycle and error behavior. The table of allocated slots verifies configured capacity. It is not a claim that every normal workload reached the theoretical peak.

The general proof supports arbitrary R and W under the stated contract. A finite model corroborates its checked cases; test coverage supports the implementation over the recorded inputs and failure paths. The new manuscript pseudocode summarizes the existing normal path and does not replace the source or error-path records.

## Allocation and process memory

The paper's 2040-to-510 KiB comparison concerns **requested boundary-pixel bytes**, with usable allocation and metadata separately reported. It is not an RSS percentage.

The earlier full-source harness did record `peak_rss_bytes` via macOS `getrusage(RUSAGE_SELF)`; see `records/CDEF_full_source_gate/scripts/ivf_gate.c`, `results/memory_results.csv`, and the original per-run logs. An earlier conversational statement that RSS had not been measured was too broad. These process high-water records exist, while the manuscript has not established a total-decoder memory-saving comparison from them. This revision preserves and indexes the records without computing a new effect size, ratio or confidence interval. Process peak RSS includes allocations beyond the CDEF boundary buffers and must be interpreted with the archived harness's input loading and output handling.

## Timing

The existing H1 design has 216 independent three-implementation blocks and 648 timed process measurements. The final reanalysis's 648 contrast-ratio rows are three ratios for each block, not 648 independent blocks. Resampling is by whole block. The existing 1.02 criterion remains primary only for hybrid/reference. Owner-pool/reference and owner-pool/hybrid remain descriptive.

Official real-content clips support the recorded output spot checks. No new real-video timing or tighter interval is claimed in this revision.
