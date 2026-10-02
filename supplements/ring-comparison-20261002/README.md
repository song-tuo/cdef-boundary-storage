# Waiting-ring comparison for CDEF

This is a separately frozen October 2, 2026 supplementary experiment. It compares a capacity-waiting identity-fixed ring with the previously evaluated dynamic token allocator. It does not replace any of the baseline/type-fix/token results in public artifact-v2.

## What is compared

Both full-source libaom v3.12.1 implementations keep the original copy sites, filtering arithmetic and consumer-return release. They allocate the same boundary-pixel capacity: min(R-1,W+1) top slots and min(R-1,W) bottom slots. The ring maps top T_j to (j-1) modulo the top count and bottom B_j to j modulo the bottom count. Before dispatch it waits, using a condition variable that releases the existing job mutex, until both required slots are free. Ring error exit wakes all waiting dispatchers. Extra condition-variable/waiter metadata is not included in the boundary-pixel count.

The experiment uses Beauty, Jockey and HoneyBee, each 60 frames of 3840x2160 8-bit 4:2:0, at W=8 and 16. Input generation and source licensing are described in the original artifact. Videos are not redistributed in this supplement. The measured host is Apple M5 Pro / arm64, Darwin 27.0.0 (recorded before timing), with macOS 27.0.1 and Apple clang 21.0.0 (clang-2100.3.34.2) recorded immediately after the run. The new build logs independently record AppleClang 21.0.0.21000334. This differs from the earlier campaign environment in the historical source-identity file. No cross-platform timing claim is made.

## Evidence layout

- `protocol/SUPPLEMENTARY_PROTOCOL.md`: analysis and execution plan fixed before formal timing.
- `protocol/FREEZE.json`, `FREEZE.sha256`, `schedule.json`: original source/binary/input/protocol lock and randomized schedule. Absolute paths identify the original host; they are retained as provenance, not expected paths on another host.
- `protocol/source_manifest.json`: hashes of both separately writable full-source trees.
- `protocol/libaom_source_identity.json`: original source archive, pinned upstream commit and configuration information.
- `patches/`: isolated type correction, original token implementation, and separate ring/common-diagnostic additions. Diagnostics are compiled out of timing binaries.
- `results/`, `logs/`: original build, correctness, sanitizer, wait, fault, recovery and timing observations, including stdout/stderr and all warmups.
- `scripts/`: unchanged campaign runners plus portable offline recalculation and source restoration helpers.

`GATES_PASS.json` covers 486 process checks: 360 synthetic release decodes, 72 sanitizer synthetic decodes, 36 natural decodes, and 18 deliberate-delay/fault/recovery cases. Synthetic release coverage is 180 configurations per implementation. Sanitizers instrument the full ring library: ASan+UBSan and TSan. ASan leak detection is disabled in this supplementary run; it is not a new leak campaign. The finite ring reservation check is additional and does not replace the general proof.

Distinct delayed dispatch rows and condition-wait calls come from one separately instrumented 60-frame pass per cell. Summed worker-wait time includes mutex reacquisition and concurrent waits; it must not be interpreted as elapsed decoder slowdown. Performance ratios use uninstrumented release binaries and the pre-specified 24 paired observations per cell.

## Recalculate without rebuilding

With Python and NumPy installed, from this directory:

```sh
python3 scripts/recompute.py
python3 scripts/ring_model.py
```

`recompute.py` checks raw pair ordering, AB/BA balance, output hashes, gate counts and exact agreement with the published six-cell summary. It computes 50,000 whole-block bootstrap resamples with the recorded seeds. It does not need the videos or original host paths. The model writes its result into `results/ring_model.json`; use a copy if preserving a byte-identical downloaded package.

## Reconstruct implementations

Supply a clean, writable copy of the recorded v3.12.1 baseline (the original source identity file records the archive and its SHA-256), then choose a new destination:

```sh
python3 scripts/restore_sources.py --baseline /path/to/aom-v3.12.1 --destination /path/to/new-source-trees
```

The helper applies the type fix and token patch separately, then the appropriate ring or optional diagnostic patch. It checks all three changed core files against the measured source hashes and refuses to overwrite an existing destination. The retained baseline includes Debian packaging files; these do not change the three audited core files. This restoration procedure was tested against the retained baseline.

## Fresh native measurements

The retained `build.py`, `gates.py`, `timing.py` and `prepare.py` preserve the original campaign, including original directory references. They are not an automatic download/install workflow. For a fresh campaign, use a separate copy, supply the three input bitstreams and synthetic inputs, and adapt only the input/output roots before freezing a new run. The native hashing harness uses macOS CommonCrypto; a port to another OS is a new environment and must be reported as such.

Build commands and compiler flags are in `results/build_*.json`. Release: CMake Release, `CONFIG_LIBYUV=0`, `CONFIG_WEBM_IO=0`, documentation off. Diagnostic profiles add `CDEF_POOL_DIAGNOSTICS=1`; sanitizer profiles use upstream `SANITIZE=address,undefined` or `thread`. After correctness gates pass, `timing.py freeze` records all sources, inputs, binaries, schedule and protocol before warmups; `timing.py timing` refuses an existing timing log; `timing.py analyze` computes the six-cell summary. Do not reinterpret setup/hash time as the primary endpoint or pool this campaign with the earlier type-fix/token campaign.

This supplement is published separately as `ring-comparison-20261002`: https://github.com/song-tuo/cdef-boundary-storage/releases/tag/ring-comparison-20261002 . Public artifact-v2 remains unchanged.

## Licensing

The libaom license, patents notice and author list accompany the patches. No blanket open-source license is asserted for the author research scripts or data; the repository LICENSING.md applies. No video, binary, complete third-party source tree or full desktop process inventory is distributed. The pre/post host summaries retain only the short busy-process lists, alongside load and version metadata. Original machine paths are retained only in experiment provenance; no credentials or account tokens are included.
