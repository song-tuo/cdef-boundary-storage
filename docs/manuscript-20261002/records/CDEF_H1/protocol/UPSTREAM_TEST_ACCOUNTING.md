# Upstream test accounting

The frozen gtest filters use the upstream default: DISABLED_ tests are not enabled, and upstream runtime CPU detection excludes unsupported ISA tests. Those records are DISABLED_NOT_EXECUTED or UNSUPPORTED, never PASS. They are not secretly executed by setting --gtest_also_run_disabled_tests. This accounting clarification is written before the remaining upstream groups finish; it changes neither source, test filters nor test selection.

For the supported selected tests, every executed test must pass. A non-disabled test that actually emits <skipped> remains SKIPPED and prevents an unqualified supported-path PASS. The safety matrix includes individual XML records and group summaries. The default-disabled upstream performance cases and runtime-unavailable SVE/SVE2 do not become failed semantic claims, but their absence limits coverage and is explicitly reported.
