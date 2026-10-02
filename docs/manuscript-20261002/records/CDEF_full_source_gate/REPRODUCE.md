# Reproduce the full-source gate

The six writable source trees are self-contained. baseline includes the three original Debian packaging patches; type_fix changes only the sizeof operand; token adds the separate ownership patch. *_audit trees add research-only metrics/fault hooks. No wrapper symbols, ABI byte offsets, or prior static archive objects are used.

Original inputs: source_archives/ contains the verified Debian source package parts. Source identity and both contribution patches are included. The full upstream test corpus remains in the main workspace and can be re-downloaded with scripts/download_testdata.py; expected official SHA-1 and measured SHA-256 identities are in tests/testdata_manifest.json. Generated input bitstreams are included. The original three reference PDFs are not redistributed.

Environment: macOS arm64, Apple Clang 21, CMake 4.4.2, Python 3.14, NumPy 2.5.3. The hashing/RSS/usable-allocation harness uses macOS CommonCrypto/getrusage/malloc_size. Primary release builds disable CONFIG_LIBYUV and CONFIG_WEBM_IO identically; codec high bit depth and both encoder/decoder remain enabled.

From this directory, run `python3 scripts/build_profiles.py baseline release`, then type_fix release and token release. Pure debug/asan/tsan builds use variant token. Research metrics/fault builds use token_audit, type_fix_audit, or baseline_audit. The scripts are explicit, not an automatic permission to change protocol thresholds.

Tests: run_correctness.py, run_upstream.py, run_shell.py, run_invalid.py, run_faults.py, run_recovery.py, and run_leaks.py record their logs/results. Read their required fixture and profile paths before running. Upstream shell version handling uses an explicit no-git shim because source distributions have no .git directory. The source code is unchanged for that workaround.

Timing: protocol/protocol.json and protocol.sha256 preserve the actual preconfirmation lock. Existing results must not be overwritten or rerun until a new independent protocol/run directory is created. `run_timing.py confirm` refuses existing results and verifies frozen executable/fixture hashes. A rebuild may produce different binary hashes; it is a new run rather than a silent reproduction of the recorded measurements.

All original failed, incomplete, interrupted, and repaired attempts are retained in logs/ and results/. See RESULTS.md for the final gate decision and exact limitations. No paper or outline was written.
