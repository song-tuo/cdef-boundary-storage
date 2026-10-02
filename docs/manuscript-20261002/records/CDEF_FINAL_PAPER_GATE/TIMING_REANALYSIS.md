# Timing reanalysis from locked H1 data

**No new timing observations were acquired.** H1 contains **648 individual measurements in 216 complete three-implementation blocks**, not 648 independent blocks. Every one of the 18 cells contains 12 complete blocks; every block has type_fix, dual_token and hybrid, with matching decoded hashes and successful recorded exits. No block was removed.

For each contrast, ratio = numerator decode_ns / denominator decode_ns within the same block. The point estimate is the median of its 12 ratios. The 95% percentile interval resamples the 12 complete blocks with replacement, 50,000 draws, preserving H1's encountered block order and seeds 311000+cell_id. The same draw indexes are used for all three contrasts in a cell. No adjacent pair is treated as an independent unit; no pooling across cells; no extra repetitions or adjusted margin.

The existing H1 balanced order and exact decode-call-plus-flush endpoint are unchanged. This is elapsed host timing on the recorded Apple M5 Pro and frozen workloads. Input preload and visible-plane hashing lie outside the timed region. Reanalysis checks reproduce every H1 primary median and interval within 1e−14. Its status remains **6 PASS / 12 inconclusive**, with margin **1.02** unchanged. All primary status labels in the CSV are inherited and verified, not newly assigned.

Both contrasts involving dual_token are **secondary/descriptive**, with no PASS, FAIL, new noninferiority decision or multiple-testing claim. The existing dual_token/type_fix cell medians range 0.986901–1.009347; dual_token/hybrid medians range 0.995081–1.025503. Every secondary interval includes one. Some are wide: dual_token/type_fix cell2 is [0.827706,1.224945]. A center near one is not an equivalence proof and does not rule out material regression. We choose to report distributions rather than the optional “no clear material regression” sentence.

The old statements “all 18 timing cells passed”, “<=2% overhead” and “zero overhead” are removed from the new paper-shaped narrative and claim ledger. Their historical presence in a locked archive is not edited or treated as current support.

## All cell estimates

Entries are median [95% block-bootstrap interval]. HT is the original hybrid/type_fix primary; DT and DH are descriptive dual_token/type_fix and dual_token/hybrid. The primary status column is H1's original result.

| Cell / workload / frame / W | HT | DT | DH | H1 status |
|---|---|---|---|---|
| 0 / waves / 1920×1080 / 2 | 1.013841 [0.874309, 1.089727] | 0.986901 [0.896133, 1.148670] | 1.025503 [0.908252, 1.143118] | inconclusive |
| 1 / waves / 1920×1080 / 8 | 1.001121 [0.870984, 1.214165] | 1.001968 [0.863603, 1.218158] | 0.995756 [0.828384, 1.220597] | inconclusive |
| 2 / waves / 1920×1080 / 16 | 1.001241 [0.827733, 1.220195] | 0.988076 [0.827706, 1.224945] | 1.000666 [0.812439, 1.206499] | inconclusive |
| 3 / waves / 3840×2160 / 2 | 0.999229 [0.973881, 1.045695] | 1.001197 [0.963832, 1.044554] | 0.998941 [0.958133, 1.044859] | inconclusive |
| 4 / waves / 3840×2160 / 8 | 0.995246 [0.942980, 1.041909] | 1.000783 [0.942177, 1.066462] | 1.004396 [0.964277, 1.059371] | inconclusive |
| 5 / waves / 3840×2160 / 16 | 0.993683 [0.934445, 1.071480] | 1.003810 [0.940299, 1.056495] | 1.003814 [0.932434, 1.060103] | inconclusive |
| 6 / checker / 1920×1080 / 2 | 0.999737 [0.968100, 1.038679] | 1.008557 [0.969860, 1.039192] | 1.000585 [0.980230, 1.038799] | inconclusive |
| 7 / checker / 1920×1080 / 8 | 1.004602 [0.978141, 1.044048] | 1.006041 [0.966678, 1.044628] | 0.999696 [0.962188, 1.038283] | inconclusive |
| 8 / checker / 1920×1080 / 16 | 1.004802 [0.968076, 1.043000] | 1.009347 [0.967875, 1.046145] | 1.000269 [0.965800, 1.040521] | inconclusive |
| 9 / checker / 3840×2160 / 2 | 1.001092 [0.995784, 1.011877] | 1.005509 [0.997765, 1.010471] | 1.002969 [0.994158, 1.009869] | PASS |
| 10 / checker / 3840×2160 / 8 | 1.000653 [0.992767, 1.012717] | 1.007140 [0.995680, 1.012865] | 1.002422 [0.993901, 1.014515] | PASS |
| 11 / checker / 3840×2160 / 16 | 1.005149 [0.995676, 1.014793] | 1.005544 [0.998216, 1.015214] | 1.002253 [0.991281, 1.009499] | PASS |
| 12 / texture / 1920×1080 / 2 | 1.007063 [0.974780, 1.032806] | 1.003082 [0.973201, 1.023450] | 0.997802 [0.974735, 1.015507] | inconclusive |
| 13 / texture / 1920×1080 / 8 | 1.007384 [0.971502, 1.041618] | 1.007778 [0.969927, 1.036106] | 0.998940 [0.967264, 1.028313] | inconclusive |
| 14 / texture / 1920×1080 / 16 | 1.006509 [0.979812, 1.039289] | 1.000704 [0.973289, 1.034120] | 0.995081 [0.964581, 1.027033] | inconclusive |
| 15 / texture / 3840×2160 / 2 | 1.004745 [0.994991, 1.010340] | 1.003666 [0.994862, 1.010306] | 1.000966 [0.994562, 1.005535] | PASS |
| 16 / texture / 3840×2160 / 8 | 1.002962 [0.994294, 1.010374] | 1.003643 [0.995712, 1.008015] | 1.000661 [0.993752, 1.003588] | PASS |
| 17 / texture / 3840×2160 / 16 | 1.004370 [0.997416, 1.010842] | 1.003824 [0.995577, 1.008754] | 0.999127 [0.994689, 1.004005] | PASS |

`TIMING_REANALYSIS.csv` retains full numeric precision and all 54 contrast-cell rows. `reanalysis/block_ratios.csv` retains all 648 raw contrast-block ratios, block IDs, numerator/denominator nanoseconds and original order. It is 648 *ratios*, not 648 independent blocks. `evidence/H1/timing_blocks.csv` preserves the 648 input measurements; `reanalysis/verification.json` records checks. The bootstrap draws are computational resampling of old observations, not new timing samples.
