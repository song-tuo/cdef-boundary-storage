# Final source and evidence audit

The retained main implementation is the original full-source **dual_token**. H1 remains **KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT**. This gate adds analysis/documents only. Old result trees, sources, protocols, inputs and papers are read-only.

## Archive and input lock

| Evidence | SHA-256 | Manifest files | CRC / bytes / SHA |
|---|---|---:|---|
| H1 | `9beba113bf719fa1c4ce68f59519a9b63cb7e29a79bc3166d28c8b596a6555e8` | 40412 | All checked; no mismatch |
| dual_token | `c7413e41262d07bf90b72a1e16a9fb3bb4b82cf6eb09c88b9b1addb9a50813e1` | 12339 | All checked; no mismatch |

Both archives were checked member by member against their manifests and the on-disk result trees, not merely against an external checksum. The H1 ZIP has 40,413 members (40,412 listed files plus manifest); the full-source ZIP has 12,340 members. The H1 manifest SHA is `85f0d8b3d61ba7a6c6af0b22f1528a9ccf0887c65427be2374655cb81ff08668`. The original manifest SHA is `03e13cca6f236923505aa4dbc0258505ebcb18e26f9d5abe15624b9b2fb41ae7`.

`evidence/LOCK_VERIFICATION.json` records paths, sizes, member counts and results. `evidence/CRITICAL_HASHES.json` separately locks 262 protocol/patch/input files. Original complete manifests, protocols, patches and selected machine tables are included in evidence/. All other upstream input hashes remain in the verified original manifests; the two large original archives are dependencies, not duplicated in the final-gate ZIP.

The first lock script used the wrong H1 decision-field name. Its KeyErrors are preserved in logs001/003; the corrected `final_state` check succeeded. No scientific data was modified. Network TLS/403/429 failures and the local PDF export's missing-class failure are also retained. A later successful check does not erase a failed attempt.

## Fixed upstream identity

| Source | Commit |
|---|---|
| libaom v3.12.1 | `10aece4157eb79315da205f39e19bf6ab3ee30d0` |
| libaom v3.15.1 | `44d0a57786f432d933ff64b653347c66f4d0fa1d` |
| H1 fixed main | `ae410fe8b7bd45f3cf61dc8f112dc783e2a08089` |

All 27 relevant Git blob IDs and SHA-256 values were independently recalculated from the existing official Git object database with `git cat-file`, including the Git blob header when recomputing SHA-1. See `evidence/SOURCE_BLOBS.json` and the exported files in `evidence/source/`. The fixed main was not moved forward during this gate. Official source: https://aomedia.googlesource.com/aom .

Across these revisions, ordered row dispatch uses the existing job mutex. Each nonfinal row preserves outgoing top and own bottom before copy-ready publication, waits for predecessor copy readiness and then filters. Return of the consuming row ends retention; producer return alone does not end the outgoing top. R is ceil(mi_rows/MI_SIZE_64X64), equivalently ceil(H/64) for coded height. W is the assigned CDEF worker count, not instantaneous busy workers.

Upstream MT allocation per plane is `sizeof(*linebuf) * R * (CDEF_VBORDER << 1) * stride`. Its sizeof operand has pointer width. The locked type_fix uses sample width `sizeof(**linebuf)` while keeping row-indexed storage. Top addresses use `row * border * stride`; bottom starts at `R * border * stride` and is also row-indexed. v3.12.1 anchors are alloccommon.c:225; thread_common.c:1195-1220 and decodeframe.c:5339. v3.15.1/main retain the allocation and addressing, with corresponding thread_common.c:1197-1222. None implements the studied worker-bounded pool.

The serial W=1 ping-pong path remains unchanged and is compatibility evidence only, as the user explicitly confirmed. The original builds share the Debian aom3.12.1-1 packaging base; eight non-CDEF packaging differences and disabled optional libyuv/WebM/documentation paths are recorded. Relevant CDEF blobs match official upstream; do not claim every file is pristine upstream.

## Semantic/safety evidence carried forward

The full-source archive retains 540 Release semantic records (180 configurations × three trees), plus 180 per Debug/ASan+UBSan/TSan profile. Its source-level allocation/copy fault and same-instance recovery records, selected conformance/row-tile/frame-parallel tests, and 36 native leak checks remain valid evidence in their recorded scope. The original broad timing conclusion is not carried forward.

H1 retains 2,592 semantic records, 1,296 hybrid debug/sanitizer records, 1,260 fault/recovery records, 27 allocation records and 81 real-content comparisons. Selected core tests are 208 per profile; selected conformance groups have 3,899 test IDs. These are recorded executions, not exhaustive library or AV1 coverage. Three resize speed cases remain disabled; runtime SVE/SVE2 and macOS LeakSanitizer remain unsupported, with native leak checks reported separately. Interrupted/failed attempts remain in the archives and are not PASS.

No new decoder, sanitizer, fault, timing or content run was performed here. Source provenance, manifest consistency and existing evidence validity were audited; this is not a fresh safety campaign.

## Closest-work clearance

`FINAL_PRIOR_WORK_MATRIX.csv` separates the ten requested dimensions. The SVT decoder allocation TODO already proposes a worker-based limit. Generic storage management is prior. No equivalent contract-plus-tight-bound contribution was identified in reviewed primary material, but CN122205106A's original publication remains unverified. The mandatory closest-work gate therefore remains incomplete and cannot support PROCEED. See `prior/REVIEW_NOTES.md` and `FINAL_DECISION.md`.
