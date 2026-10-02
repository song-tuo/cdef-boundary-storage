# Existing dav1d evidence used in the final wording

The paragraph uses the previously frozen audit at commit `9a275d0c9296f2c0ded9d0dd28f99cf22dea2572`. The eight retained source-file hashes were checked against that audit before this insertion; no formula checker or decoder was executed.

| Manuscript statement | Original source anchor |
|---|---|
| Process the band above a superblock row and defer the final band, except at frame end | `src/recon_tmpl.c:2038-2050`: `p_up`, `start - 2`, and `n_blks = sbsz - 2 * (sby + 1 < f->sbh)` |
| Task-threaded boundary snapshots are shared with restoration without resizing, and separate with resizing | `src/cdef_apply_tmpl.c:211-280`: `have_tt`, `resize`, `lr_lpf_line`, and `cdef_lpf_line` branches for luma/chroma |

Primary source: [fixed dav1d source tree](https://github.com/videolan/dav1d/tree/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src).
The preserved [full audit](https://github.com/song-tuo/cdef-boundary-storage/blob/artifact-v4/evidence/dav1d/README_HISTORICAL.md) records the producer/consumer distinction, allocation formula and exclusions. Its analytical examples remain outside the manuscript. The new paragraph reports a contract difference, without a memory or throughput ranking or transfer of the libaom bound.
