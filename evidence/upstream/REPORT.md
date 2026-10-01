# Bounded current-upstream persistence gate: PASS

Official v3.15.1 and pinned main preserve the row-indexed allocation, pointer-width sizeof expression, and normal copy-ready synchronization contract. Both original patches apply cleanly with zero fuzz. All complete source blobs were materialized, writable, and matched their official Git tree: 1,520 for the release and 1,523 for main.

The release is dated 2026-09-21 in its release notes; its annotated tag was created on September 22. The main snapshot was retrieved on 2026-09-30 local time. Identities and source-level proof are in results/source_identity.json, results/source_audit.json and SOURCE_SEMANTICS.md. The tag signature was retained but not independently verified.

Six isolated pure Release builds passed (baseline/type_fix/token × release/main); six additional separate allocation-audit builds passed. Each pure build includes the default full encoder, decoder, and upstream test executable. Audit builds compile the full library and add only diagnostic reporting to decodeframe.c.

Correctness: **228/228** smoke decodes matched the archived v3.12.1 baseline, covering 18 depth/chroma/edge fixtures and one 4K waves stream at W=8/16, row_mt=1. Conformance: **242/242** upstream single-thread AV1/TestVectorTest cases per pure build, **1452** passing test executions. All **480/480** distinct vector/reference files matched the current upstream SHA-1 manifest. This is the bounded group specified in PROTOCOL.md.

Allocation checks passed in all 12 version/variant/worker configurations; every run decoded all 18 frames with 17 actual CDEF invocations and a matching pure-build output digest.

| Version | Workers | Baseline bytes | Type-fix bytes | Token bytes |
|---|---:|---:|---:|---:|
| v3.15.1 | 8 | 8,355,840 | 2,088,960 | 522,240 |
| v3.15.1 | 16 | 8,355,840 | 2,088,960 | 1,013,760 |
| main | 8 | 8,355,840 | 2,088,960 | 522,240 |
| main | 16 | 8,355,840 | 2,088,960 | 1,013,760 |

These measured requested allocations reproduce the v3.12.1 storage values on both newer source snapshots. They support source persistence and bounded compatibility; they do not replace the full original evidence or establish newer-version timing or sanitizer results.

The two separate source patches and suggested review descriptions are ready for author inspection in patches/ and UPSTREAM_REVIEW_PREPARATION.md. They are not uploaded or accepted; verified author email, contributor requirements, and author approval remain human steps.

Protocol, frozen runner hashes, command/exit logs, output digests, GoogleTest XML, all per-frame allocation events, source blob verification, and build compile commands are retained. Setup failures are disclosed in REPORT.json and did not remove any executed test result.
