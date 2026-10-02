# Evidence for the 2026-10-02 CDEF manuscript

**An Exact Storage Bound for Row-Parallel CDEF in the AV1 Decoder**, Song Dong.
This release aligns the manuscript with the already completed full-source, H1 and FINAL records. It adds no implementation, decoding, timing, bootstrap or scientific gate. `manuscript_identity.json` identifies the exact TeX and PDF.

## Start here

- [EVIDENCE_MAP.csv](EVIDENCE_MAP.csv): each figure, table, principal number and claim mapped to existing files and selectors.
- [RESOURCE_ACCOUNTING.md](RESOURCE_ACCOUNTING.md): requested/usable allocation categories and the separate historical RSS endpoint.
- [CONTRACT_SOURCE_EVIDENCE.md](CONTRACT_SOURCE_EVIDENCE.md): source functions, retained command names and audit semantics.
- [VERIFY.md](VERIFY.md): verification-only commands and original execution entry points.
- [EXPORT_LINEAGE.json](EXPORT_LINEAGE.json): original/export hashes; path-only redactions.

## Version correspondence

| Manuscript location | Current evidence | Earlier artifact-v2 description |
|---|---|---|
| Table I | Owner-pool correctness/safety, original full-source gate | Not the six-row allocation table described by v2 |
| Table II | Four allocation rows from H1 | Not v2's twelve-row natural-video timing table |
| Table III | Closest-work comparison and source notes | No experimental timing table |
| Section IV-C | H1: 216 independent blocks, 648 timed processes, 18 cells | v2 natural-video timing is a different experiment |

The original v2 files and tag remain historical artifacts. Its 8K analytical projections and natural-video timing are not evidence for the current paper's tables or timing claims.

## Scientific interpretation

`token` in the original full-source gate and `dual_token` in H1 denote the paper's owner pools. `type_fix` is its sample-size-correct reference. H1 remains **KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT**: six primary hybrid/reference cells pass the fixed 1.02 criterion, twelve are inconclusive. Owner-pool contrasts remain secondary/descriptive. Historical PASS wording in older reports does not supersede this interpretation.

The archived FINAL decision preceded original-document clearance of CN122205106A. The later CN clearance is retained separately; neither historical decision is rewritten.

## Repository and release ZIP

The Git repository contains this guide, protocols, source anchors, selected source, scripts and result records. All preserved command stdout/stderr and log files are supplied in the `CDEF_current_manuscript_evidence.zip` asset of [artifact-v3](https://github.com/song-tuo/cdef-boundary-storage/releases/tag/artifact-v3). File membership and hashes are listed in each distribution's manifest. Full media, compiled binaries and upstream source archives are omitted; input/source identities and acquisition manifests are retained. Empty/malformed failure-test IVF fixtures are also excluded and indexed in `EXCLUDED_FILES.json`.

The complete original local result archives are identified in `ORIGINAL_ARCHIVES.json`; they are not this release asset. Historical source/input hashes continue to identify original bytes. `EXPORT_LINEAGE.json` identifies path-redacted exports separately. Private workflow files, reference PDFs and the unpublished manuscript itself are not distributed.
