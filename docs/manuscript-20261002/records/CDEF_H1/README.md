# CDEF-H1 SIMPLE-BOTTOM / HYBRID CONFIRMATORY GATE

This is a new, independent H1 result tree. U and AL remain stopped. No prior CDEF/U/AL result is overwritten.

Read RESULTS.md and decision.json for the final decision, then PROTOCOL_FROZEN.md, SOURCE_DRIFT_AUDIT.md, HYBRID_DESIGN.md and THEORY_CHECK.md. The exact user-confirmed W=1 scope is in protocol/USER_SCOPE_CONFIRMATION.md. W=1 preserves upstream serial behavior and is a compatibility control; tight capacity acceptance is for actual row-MT W=2,8,16.

The CSV files retain every requested setting and outcome. COMMANDS.json indexes experiment/build/acquisition commands, UTC starts, environment deltas, stdout, stderr and exit codes. Under logs/, expected injected decoder errors remain errors with their original text; a successful fault-handling test does not erase them. Skipped/unsupported entries are explicit and not PASS.

src/ contains separate clean, audit and accounting source trees. All are based on the same libaom v3.12.1 lineage, with inherited disabled-feature packaging differences disclosed in PATCH_LEDGER.md. Only the clean Release binaries supply timing. Full-library Debug and sanitizer binaries independently validate hybrid. Official upstream source archives, relevant Git blob identities and patches are included.

Timing is new: 18 cells, 12 complete three-implementation blocks per cell, six balanced permutations each twice, and whole-block bootstrap. Old token timing confidence intervals are not used. Findings apply only to the frozen local workloads and host. Boundary allocation request/usable bytes are not RSS, SRAM, area, power or energy.

The result ZIP includes source, patches, generated/fixed H1 inputs, executables/libraries, build configurations, all command logs and machine results. Disposable object files, dSYM caches, the bare Git object database and the read-only 3.4 GiB upstream fixture cache are excluded. inputs/upstream_fixture_manifest.json supplies official URLs, expected SHA-1 and newly verified SHA-256 for that cache; fixed real-content sources and H1-derived conformance payloads are included. MANIFEST.json covers every packaged payload file; the ZIP has a separate SHA-256 and CRC verification record.

Scripts use the new result root and reject overwriting command logs. Reproduction should use a fresh root, preserve the frozen protocol, and rebuild from recorded source/configuration; do not rerun mutating source-preparation steps inside this completed tree.
