# Polished manuscript and evidence map, 2026-10-02

This capsule identifies the four-page **An Exact Storage Bound for Row-Parallel CDEF in the AV1 Decoder**, by Song Dong, after its bibliography corrections. `manuscript_identity.json` gives the exact final PDF and TeX hashes. The paper itself is not distributed here.

## Read this map for the current paper

- Table I: original full-source output, concurrency and failure/recovery validation.
- Table II: four recorded allocation rows plus three starred analytical 8K rows. The 8K assumptions are in `support/ANALYTICAL_8K.json`; those rows are calculations, not new decoder runs.
- Table III: related-source comparison.
- Section IV-C: the fixed H1 timing collection (216 independent blocks, 648 process observations). The actual implementations are `type_fix`, `dual_token`, `hybrid`. The owner-pool/reference comparison is secondary and descriptive. Rounded displayed values refer to the same original medians and intervals.

`EVIDENCE_MAP.csv` maps individual claims to records. `SUPPORTING_DETAILS.md` preserves the original hybrid primary outcome (six passes, twelve inconclusive cells at margin 1.02). H1 remains **KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT**. `RESOURCE_ACCOUNTING.md` keeps boundary allocations distinct from historical process-memory endpoints.

## Relationship to earlier versions

The immutable artifact-v4 map describes an earlier five-page manuscript, not this four-page Polished revision. This capsule updates manuscript identity, table numbering, wording and bibliography locators. The complete scientific evidence remains the exact [artifact-v3 evidence ZIP](https://github.com/song-tuo/cdef-boundary-storage/releases/download/artifact-v3/CDEF_current_manuscript_evidence.zip), identified by `EVIDENCE_BASE.json`. The v4 dav1d source evidence remains under `evidence/dav1d/` in this repository.

No experimental record, patch, frozen protocol, statistical result or decision was changed. The earlier tags and maps remain available. This update does not claim that every historic file under the repository root describes the current paper.

Run `python3 verify.py` in this directory to check this capsule. Optionally add `--evidence-zip /path/to/CDEF_current_manuscript_evidence.zip` to check the exact reused evidence asset and locators. This performs integrity checks only.
