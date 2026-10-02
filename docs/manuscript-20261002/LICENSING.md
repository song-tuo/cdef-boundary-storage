# Licensing and provenance

This is a research artifact prepared for public reproducibility. Public availability is not, by itself, an OSI open-source license grant.

- The libaom patch context and source-derived code are accompanied by the upstream BSD-style `third_party/libaom/LICENSE` and `PATENTS` notices. Their terms continue to apply to the third-party material. New patch contributions are not represented as accepted or licensed by AOMedia.
- The dav1d literal `decode.c` expressions and source-derived arithmetic in `evidence/dav1d/verify_formula.py` (also imported by `tools/dav1d_formula.py`) retain the complete VideoLAN/dav1d and Two Orioles BSD-2 notice in `third_party/dav1d/decode.c-notice.txt`; `PROVENANCE.json` identifies the pinned source and notice lines. The libaom license does not substitute for this notice.
- The three Debian patches and their original copyright/license metadata are retained under `third_party/`. The Debian copyright file lists component-specific licenses; this artifact does not replace them with a blanket license.
- The original research helper scripts, new portability tools, proof/algebra helpers and measurement data have no additional author-selected open-source license in this package. The package maintainer must choose an applicable grant before presenting them as open-source software. No third-party ownership or grant is invented here.
- UVG video is not bundled. Its separate CC BY-NC 3.0 source license and required attribution are recorded in `evidence/natural/sources/ATTRIBUTION.md`. The downloader does not change that license. Raw or re-encoded video must be handled under the source terms.
- Python, NumPy, py7zr, libcrypto and build-tool dependencies are not bundled. Their licenses remain those of their respective projects.

`historical/` contains reference research sources; `tools/` contains newly adapted portability/recalculation sources. Original/export hashes in the provenance manifest document their source lineage. None of the private workflow definitions or reference documents used during development are included.

The artifact-v3 supplement contains previously recorded CDEF/H1/FINAL data and author-written guides. It bundles no UVG or AOM video, third-party paper PDF, private workflow or full upstream source distribution. Existing notices and the absence of an additional author-selected blanket license remain unchanged.
