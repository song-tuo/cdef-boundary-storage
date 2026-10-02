# CDEF boundary-storage research artifacts

## Separate waiting-ring supplement (October 2, 2026)

For **Worker-Bounded Boundary Storage for Row-Parallel AV1 CDEF Decoding**, a new [ring/token supplement](supplements/ring-comparison-20261002/README.md) compares six 4K natural-video cells at matched boundary-pixel capacity. It preserves the original artifact-v2 results, adds independently frozen timing and wait diagnostics, and includes raw logs and offline recomputation. See the dedicated [ring-comparison-20261002 release](https://github.com/song-tuo/cdef-boundary-storage/releases/tag/ring-comparison-20261002). This supplement does not replace the manuscript maps below.

## Current manuscript: artifact-v5

The four-page Polished manuscript with corrected references is identified by [the v5 manuscript map](docs/manuscript-polished-20261002/README.md). It maps Table I validation, the combined recorded/analytical Table II, Table III related sources and the secondary descriptive owner-pool timing comparison. Exact PDF/TeX identities are recorded; the manuscript itself is not published here. All experimental evidence remains unchanged.

## Previous wording: artifact-v4

The final wording of **An Exact Storage Bound for Row-Parallel CDEF in the AV1 Decoder** is identified by [this manuscript map](docs/manuscript-final-20261002/README.md). It clarifies fixed-address motivation and hybrid definitions, adds the existing dav1d contract comparison, and groups Table I by the property checked. All scientific evidence and decisions are unchanged. The small v4 mapping capsule references the exact full evidence ZIP from v3; no new experiment or analysis was run.

## Previous wording: artifact-v3

For **An Exact Storage Bound for Row-Parallel CDEF in the AV1 Decoder** (2026-10-02), start with [the manuscript-specific evidence map](docs/manuscript-20261002/README.md). It identifies the exact manuscript hashes, Table I safety coverage, Table II four-row allocation table, Table III source comparison and Section IV-C H1 timing. The [artifact-v3 release](https://github.com/song-tuo/cdef-boundary-storage/releases/tag/artifact-v3) supplies the complete exported command logs.

This update publishes existing evidence and corrects the version correspondence; it runs no new experiment or analysis. H1 remains KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT (6/18 primary passes, 12/18 inconclusive). The owner-pool comparison remains secondary/descriptive.

The instructions and table descriptions below belong to **artifact-v2**, a different manuscript snapshot. Its 8K projections and natural-video timing are not the current manuscript's tables. The immutable [v2 tag](https://github.com/song-tuo/cdef-boundary-storage/tree/artifact-v2) preserves those original files. The current root SHA256SUMS covers this checkout; the older checksum file is retained as provenance/artifact-v2-SHA256SUMS.

---

# Worker-Bounded Boundary Storage for Row-Parallel AV1 CDEF Decoding

This research artifact provides the two separate libaom v3.12.1 patches, the recorded measurements behind the two paper tables, and tools for recalculation and new core correctness/allocation runs. It preserves the strong comparison: **type-fix versus token**. The pointer-size correction is a separate baseline change.

## Check the static-placement proposition

```sh
python3 tools/static_placement_check.py
```

This standard-library-only finite model checks 40 configurations, R=1..10 and W=1..4: simultaneous peak capacity, both pool maxima in one state, and the exact static address count from the union conflict graph. The supplied original, maintained version provenance, and successful outputs are documented in `evidence/static_placement/README.md`. The general proof remains the mathematical basis of the result.

## Start with offline recalculation

Requires Python 3.12+ and NumPy; the recorded reference analysis used Python 3.14 and NumPy 2.5.3. From this directory:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-analysis.txt
.venv/bin/python tools/recompute.py --out computed
.venv/bin/python tools/dav1d_formula.py
```

`computed/table_1_boundary_capacity.csv` reproduces all six rows of Table I, including the two explicitly analytical 8K projections. It checks the four measured allocations against both the synthetic and natural audit records. `computed/table_2_natural_timing.csv` reproduces all twelve rows of Table II from individual paired observations with the original seeds and whole-block resampling. It also recomputes every original synthetic interval, including the six large-delay controls, and the separately labeled post-hoc block diagnostic.

The recalculation verifies the exported evidence hashes, all **624 natural timing per-process records/stdout**, all **72 correctness/allocation records**, every balanced AB/BA block, the **312 natural pairs** including 24 warmups, the **312 synthetic pairs** including controls/warmups, and the **90 original memory records**. It performs no new timing measurements. The output `checks.json` states the checked counts.

## Prepare six isolated source/build configurations

Requirements: a C/C++ compiler, CMake, Make or Ninja, Git, Perl and `patch`. An x86 build additionally needs the assembler required by libaom (NASM/Yasm). The portable harness uses CommonCrypto on macOS and OpenSSL (`libcrypto` development headers) on Linux. The Linux portability branch has not been validated by a Linux campaign.

Choose an empty work directory **outside `evidence/`**:

```sh
python3 tools/source_build.py prepare --work work
python3 tools/source_build.py build --work work --jobs 4
```

Preparation downloads the Debian `aom_3.12.1.orig.tar.gz` archive and checks its fixed SHA-256. If it is already available, pass `--archive /path/to/aom_3.12.1.orig.tar.gz`. The orig archive's 1,347 corresponding files were previously checked against upstream v3.12.1 commit `10aece4157eb79315da205f39e19bf6ab3ee30d0`. The three retained Debian patches affect documentation and CLI library integration. All configurations disable the same doc/libyuv/WebM options. See `provenance/source_identity_v3.12.1.json`.

Preparation creates `baseline`, `type_fix`, `token` and three separate `_audit` source trees. The first patch changes one `sizeof` operand; the second implements the bounded storage and is applied on top of type-fix. The build command creates a separate Release static library, programs, compile database and `ivf_gate` harness for each tree. Audit builds report CDEF activity and requested/allocator-usable bytes and contain the historical fault hooks. Their stage times are not the primary performance endpoint.

The public tools are portability adaptations. They do not replace the original source/executable hashes in the historical evidence and do not claim byte-identical binaries across platforms.

## Run a small new correctness/allocation check

```sh
.venv/bin/python tools/generate_synthetic.py work smoke
.venv/bin/python tools/core_smoke.py --work work
```

The fixed smoke generates a two-frame 4K 8-bit 4:2:0 stream and checks W=8/16 across all six configurations (12 fresh processes): frame count, visible-pixel hash equality, positive CDEF activity and formula-matching boundary allocation. It reports **correctness and allocation only**, not a new performance result. Fresh outputs go to `work/runs/core_smoke`; an existing output directory is not overwritten.

The generator also accepts `correctness`, `timing`, or `pilot` instead of `smoke` to regenerate the original synthetic recipes. Those names select input recipes; generating them does not rerun the historical campaigns. Reference stream hashes are retained in the evidence. A different platform/compiler may produce different encoded bytes; record that deviation rather than calling a new bitstream the original frozen input.

## Obtain and encode the natural inputs

Natural acquisition also requires the `curl` command. The UVG source material is separately distributed under CC BY-NC 3.0. Read `evidence/natural/sources/ATTRIBUTION.md` and the official dataset license before downloading. Video media are deliberately absent from this repository.

```sh
.venv/bin/pip install -r requirements-acquisition.txt
.venv/bin/python tools/fetch_natural.py work
.venv/bin/python tools/prepare_natural.py work
.venv/bin/python tools/core_smoke.py --work work --run-name natural_beauty_4k \
  --input work/natural/media/Beauty_3840x2160_first60.ivf \
  --width 3840 --height 2160 --frames 60
```

The distinct run name preserves the earlier smoke outputs while reusing the same six build configurations.

The downloader acquires exact first-60-frame raw prefixes of Beauty, Jockey and HoneyBee using cached HTTP ranges in their official 7z archives. About 1.2 GB of compressed ranges and 2.8 GB of original/downsampled raw input were used historically. Whole-archive/member CRC is not claimed for this partial acquisition. Source-prefix length and SHA-256 must match the retained reference; 1080p is a fixed per-plane 2×2 box downsample. The encoder uses the original fixed settings, checks regenerated bitstream hashes against the historical values, and writes new input manifests outside the evidence.

The published historical natural runner is retained under `historical/natural/` for method inspection. It contains archival layout and hash-lock assumptions and is **not the portable entry point**. This package supplies full offline timing reanalysis and fresh core correctness/allocation checks; it does not automate a new complete 624-process performance campaign or a complete repeat of upstream tests, sanitizers, fault/recovery and leaks. A new campaign needs its own prospective protocol and quiet-host coordination. Do not overwrite, refreeze or merge it into these historical observations.

## Evidence layout and interpretation

- `patches/v3.12.1/`: independently identifiable type-fix and token increments.
- `evidence/natural/`: frozen protocol/input/schedule exports, all raw outcomes, source attribution and analysis summaries. Twelve cells, three source scenes, six streams; each source prefix is 0.5 s at 120 fps.
- `evidence/synthetic/`: original protocol, raw timing/memory and selected correctness/safety records, upstream XML including initial failures/retries.
- `evidence/upstream/` and `patches/upstream/`: bounded v3.15.1 and pinned-main compatibility results and patches; they are not full repeats of the v3.12.1 campaign.
- `evidence/dav1d/`: fixed-source allocation algebra audit and analytical examples. `tools/dav1d_formula.py` rechecks the algebra; `--source-dir` optionally verifies a separately obtained dav1d checkout against the eight recorded file hashes. This is not a decoder benchmark.
- `docs/upstream-report/`: the sizeof bug report and minimal reproducer prepared on October 1. Its status is as recorded there; no upstream acceptance is implied.
- `historical/`: original research helper sources retained for lineage, separate from the runnable portability tools.
- `provenance/export_lineage.json`: source/export hashes and the exact path-only transformation applied to each retained evidence file.

The primary timing endpoint is cumulative wall time inside `aom_codec_decode` including final flush. Input loading, initialization, output retrieval/hash, destruction and process startup are outside it. The natural estimator is the median of 24 paired ratios, with 12 balanced two-pair blocks and pointwise 95% bootstrap intervals. The values are not ratios of marginal medians or CDEF-only speed measurements. Requested, usable and process RSS are distinct memory endpoints.

See `docs/HISTORICAL_SCOPE_AND_FAILURES.md` for retained failures, controls and limits. The historical protocol was frozen locally before its measured campaign; this package is an October 1 portability/export step, **not a new preregistration**.

## Export integrity and licensing

Historical records with private machine paths use declared tokens such as `${FULLSOURCE_ROOT}` and `${NATURAL_ROOT}`. Only path substrings were replaced: measurements, timestamps, seeds, case identifiers, statuses, failures and exclusions remain intact. `export_lineage.json` binds original and exported bytes separately. Original hashes inside an exported frozen lock still identify the original bytes; they should not be mistaken for exported-file checksums. The private reverse map is not distributed.

No complete source tree, video, binary, private workflow material or third-party paper is included. Third-party notices are in `third_party/`. No blanket open-source license is asserted for the author research scripts, patches or data; see `LICENSING.md` for the explicit status.
