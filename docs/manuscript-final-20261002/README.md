# Final wording and evidence map, 2026-10-02

**An Exact Storage Bound for Row-Parallel CDEF in the AV1 Decoder**, Song Dong.

This is the fixed evidence entry for the final wording revision. `manuscript_identity.json` gives the exact local manuscript PDF/TeX hashes. The paper itself is not published here.

## What changed

1. The introduction explicitly motivates row-modulo addressing and the distinction between peak occupancy and conflicts across all legal schedules.
2. The hybrid is defined before first use, with its role as the simpler implementation tested by H1.
3. A short dav1d paragraph uses an existing fixed-source audit to explain different boundary lifetimes.
4. The abstract is more direct, and Table I groups the same coverage counts by the property tested.

The theorem, proof, proposition, figure, allocation table, related-work table and runtime paragraph are unchanged. All experiments, estimates, intervals and decisions retain their previous values. H1 remains **KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT**: six primary hybrid/reference passes and twelve inconclusive cells at 1.02; owner-pool comparisons remain secondary/descriptive.

## Evidence

Read [EVIDENCE_MAP.csv](EVIDENCE_MAP.csv). Its `evidence_root` distinguishes the two locations:

- Existing full-source/H1/FINAL results and all exported command logs are in the **unchanged** [artifact-v3 evidence ZIP](https://github.com/song-tuo/cdef-boundary-storage/releases/download/artifact-v3/CDEF_current_manuscript_evidence.zip). Its exact SHA-256 and size are in [EVIDENCE_BASE.json](EVIDENCE_BASE.json). The v3 guide's manuscript hash describes the previous wording; the identity in this directory describes the current wording.
- The dav1d source audit is already in the repository under `evidence/dav1d/`. [DAV1D_SOURCE_NOTES.md](DAV1D_SOURCE_NOTES.md) maps the new paragraph to source operations.

The [v3 resource account](https://github.com/song-tuo/cdef-boundary-storage/blob/artifact-v3/docs/manuscript-20261002/RESOURCE_ACCOUNTING.md) still applies: H1 requested/usable allocations and historical process-peak RSS remain separate endpoints.

## Verification only

Run `python3 verify.py` here to verify this capsule. To verify the unchanged evidence asset and the mapped file paths, run `python3 verify.py --evidence-zip /path/to/CDEF_current_manuscript_evidence.zip`. The script performs file/hash checks only. It does not execute decoding, timing, resampling or the dav1d algebra checker.

The v4 release asset is a small manuscript-mapping capsule. It deliberately references the existing v3 full evidence ZIP instead of republishing or regenerating its scientific outputs. Earlier v2/v3 tags and files remain intact. Existing repository licensing terms apply.
