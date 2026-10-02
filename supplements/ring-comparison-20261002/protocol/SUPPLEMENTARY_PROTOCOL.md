# Ring-versus-token supplementary comparison

This protocol specifies a new comparison before any confirmatory ring/token timing. Historical type_fix/token evidence stays unchanged. All new observations, including null or adverse results, are retained.

## Implementations

Two copied, separately writable libaom v3.12.1 full-source trees originate from the existing validated token source. The token allocator remains the evaluated dynamic allocator. Ring uses identity-fixed top slot (reader-1) mod min(R-1,W+1) and bottom slot reader mod min(R-1,W), ordered reservation before dispatch, and waits for both slots via a condition variable under the existing job mutex. Waiting atomically releases the mutex. Return broadcasts only when waiters exist; decoder-error exit broadcasts and aborts waiting dispatch. Copy sites, pixel arithmetic and consumer-return release sites are unchanged. Both have the same boundary-pixel allocation. Ring adds its condition variable and waiter metadata; bookkeeping is not asserted equal.

Common optional diagnostic code is compiled out of the release timing builds. It counts dispatch rows, distinct rows delayed before dispatch, condition-wait calls, and summed worker wait time including mutex reacquisition; the last is not critical-path time. No busy waiting. Instrumented builds are for correctness, wait frequency and stress only.

## Correctness before timing

- Finite reservation model: R=1..10, W=1..4; no slot alias or nonterminal deadlock.
- Normal release decode: all original 180 synthetic configurations and three 4K natural inputs at W=8/16 must match retained pixel hashes/frame counts.
- Diagnostic ring and token: same six natural cells; equal allocation and positive CDEF activity. Record waits without removing outlying frames.
- Whole-library ASan+UBSan and TSan ring builds: representative boundary/format/worker configurations and six natural cells. Stress delayed row 1 after filter and before release, and injected error at that site, to exercise wakeup and abort. Failures stop confirmatory timing; repaired versions are recorded and revalidated.

## Primary timing

- Inputs: existing 60-frame 4K 8-bit 4:2:0 Beauty, Jockey and HoneyBee bitstreams; hashes locked before timing. No new encoding.
- Workers: 8,16; row-MT=1. Six cells.
- A=token release, B=ring release. Both built now from full source with the same compiler/configuration; separate libraries/harnesses, no diagnostics or delay environment variables.
- Per cell: two warmup pairs plus 24 analyzed pairs in twelve two-pair blocks. Each block contains one AB and one BA pair. Shuffle cells per block and pair order with Python random seed 2026100207. Warmup is block -1.
- Fresh process for every observation. Primary endpoint is cumulative monotonic wall time within decode calls including flush, identical to the retained harness; file loading, initialization, frame hashing/retrieval and destruction are outside it. Fixed 0.20 seconds between processes. Timeout=120 seconds; any timeout, nonzero exit, frame/hash mismatch stops the run, with all partial observations retained. No data-dependent exclusions or repeat replacement.
- Estimator: median paired ring/token ratio; pointwise 95% percentile interval from 50,000 whole-block bootstrap resamples, NumPy default_rng seed 2026100208+cell and linear quantiles. Include all 24 analyzed pairs. Descriptive comparison: no claimed universal speed advantage or cross-platform equivalence; report every cell whether it favors ring, token or neither.
- Record process snapshots and load before/after; do not run build/sanitizer/download jobs concurrently. Final source manifests, executable/library/stream hashes, protocol and exact randomized schedule must be sealed in FREEZE.json before the first warmup process. Subsequent hash changes invalidate the run; preserve failures and restart only as a separately identified campaign.

## Scope

This experiment estimates the practical cost of capacity waiting under this workload. It does not prove that dynamic allocation is always faster or uniquely necessary, and it does not establish a memory-constrained device benefit. No new hardware-cost claim. Public artifact-v2 remains the source of the original results; new files will be packaged separately for review and will require explicit publication before any public-availability claim.
