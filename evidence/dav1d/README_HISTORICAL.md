# Pinned dav1d CDEF allocation audit

This is a source-level allocation audit of commit
`9a275d0c9296f2c0ded9d0dd28f99cf22dea2572`, already fixed in
`revision_20260930/related_work/source_ledger.json`. All eight retained dav1d
files still match that ledger's original SHA-256 values. In particular,
`code/dav1d_src_decode.c` has SHA-256
`2acdee23ed5c6e59300bcb8cbd22ad61252f2d1aaaf7c42f79b993472fff5d4a`.
No network operation, HEAD refresh, download, build, decoder run, or paper
edit was performed. The three Priority-0 literature sources remain closed.

## Exact requested-byte expression

Let

- `s_Y = f->cur.stride[0]` and `s_UV = f->cur.stride[1]`, in **bytes per row**;
- `S = f->sbh`, the number of superblock rows;
- `b = f->seq_hdr->sb128`, either zero or one;
- `H = f->frame_hdr->height`, in luma pixels;
- `r = 1` iff `c->n_tc > 1` and `width[0] != width[1]`, otherwise zero.

The size argument passed for `cdef_line_buf` is

\[
A_{\mathrm{CDEF}}=64+2^r S\bigl(4|s_Y|+8|s_{UV}|\bigr)\quad\text{bytes},
\qquad
S=\left\lceil\frac{H}{64\,2^b}\right\rceil.
\]

This follows literally from `decode.c:2906-2918`. Multiplication binds
before the left shift, and `need_cdef_lpf_copy` is a Boolean, so the shift
multiplies each stride term by `2^r`. The **64 bytes are not doubled**.
The allocation uses 32-byte alignment and advances its working pointer by
32 bytes (`2918,2924`). The formula states the requested size; allocator
metadata, allocator rounding, and process RSS are outside it. It excludes
the separate `lr_line_buf`, frame images, stack scratch, and other decoder
buffers. It is per frame context, not a total across frame contexts.

The ordinary region reserves two two-line luma banks per superblock row
(`4|s_Y|S`) and two two-line banks for each of the two chroma planes
(`8|s_UV|S`). The pointer views are assigned at `2924-2942`. When `r=1`,
the following region reserves four luma and four lines per chroma plane
for `cdef_lpf_line`, adding the same stride-dependent size (`2945-2957`).
These allocations establish capacity, not a minimum simultaneous-live
set. In particular, their array dimensions alone do not prove tightness.

`f->cur` is the coded-width picture: resizing creates it using `width[0]`,
while the restored/upscaled picture is `f->sr_cur.p`
(`decode.c:3527-3546`). The formula therefore uses the **coded picture's
actual byte strides**, including padding and signed orientation. Using
display width or the `sr_cur` stride would be wrong when resizing changes
the width. The byte stride already includes sample storage width, so do
not multiply the formula by another factor for bit depth. The code uses
`PXSTRIDE` when converting those byte strides to pixel-pointer offsets
(`cdef_apply_tmpl.c:121-122`), corroborating the unit distinction.

## Superblock rows and branch conditions

`decode.c:3562,3565-3567` computes

\[
\mathrm{bh}=2\left\lceil H/8\right\rceil,
\quad \mathrm{sb\_step}=16\,2^b,
\quad
S=\left\lceil\frac{2\lceil H/8\rceil}{16\,2^b}\right\rceil
=\left\lceil\frac{H}{64\,2^b}\right\rceil.
\]

The last identity uses that `8*2^b` is an integer. Thus 64-pixel
superblocks give `ceil(H/64)` rows and 128-pixel superblocks give
`ceil(H/128)` rows. This `S` must not be identified with the manuscript's
fixed 64-pixel libaom filter-row count without checking `b`.

| Task contexts | Horizontal resize | `r` | Size requested |
|---|---|---:|---|
| `n_tc = 1` | absent or present | 0 | `64 + S(4|s_Y| + 8|s_UV|)` |
| `n_tc > 1` | absent | 0 | `64 + S(4|s_Y| + 8|s_UV|)` |
| `n_tc > 1` | present | 1 | `64 + 2S(4|s_Y| + 8|s_UV|)` |

The relevant condition is task-context count `n_tc`, not frame-context
count `n_fc` or an assumed correspondence to libaom's `W`.
Changing the task count from two to eight does not multiply the request.
Changing whether it exceeds one can change the extra-copy flag when
resizing is present.

In `dav1d_decode_frame_init`, the old buffer is freed and reallocated only
when a cached signed stride product, the extra-copy flag, or `S` changes
(`decode.c:2909-2914,2961-2964`). Otherwise the existing storage is reused.
The allocation block itself is not guarded by the CDEF-enabled flag;
this audit describes executions that reach it. Actual CDEF work is gated
separately (`thread_task.c:830-833`, `recon_tmpl.c:2027`).

Even with `n_tc=1`, this requested capacity retains the factor `S`. In
the filtering code, `have_tt=0` suppresses the per-row pointer offset
(`cdef_apply_tmpl.c:118,129-138,232-235,277-280`), but this smaller active
view does not alter the allocation formula. For fixed nonzero strides,
the requested size is linear in `S` (hence `O(S)`). With varying width,
write `O(S(|s_Y|+|s_UV|))`. This is an allocation result, not a live-storage
lower bound or a whole-decoder memory-complexity claim.

## Contract difference from the manuscript

The manuscript's libaom model retains whole prefilter top/bottom strips
until the corresponding row-filter returns, under its specific ordered
issue and copy-ready dependency. Its theorem is
`K = min(2R-2, 2W+1)` for that event/retention contract.

The pinned dav1d path has different producers, consumers, and releases:

1. The deblock-row wrapper calls `dav1d_copy_lpf` to save pixels needed
   by CDEF and restoration (`recon_tmpl.c:2005-2022`). With zero signaled
   luma deblocking levels and snapshots required, the scheduler uses
   `copy_lpf_progress` to wait for the preceding superblock row; with
   nonzero levels, deblock progress supplies the dependency
   (`thread_task.c:793-828`). Do not characterize every path as using the
   copy flag.
2. The CDEF wrapper first filters the eight-luma-pixel band above the
   current superblock row, when present, then processes the current row
   with its final band deferred except at the frame end
   (`recon_tmpl.c:2038-2050`). The inner loop advances by eight luma
   pixels and saves two prefilter lines (`cdef_apply_tmpl.c:124-138`).
3. In the task-threaded path, the boundary inputs reuse `lr_lpf_line`
   without resizing, and use separate `cdef_lpf_line` snapshots with
   resizing (`cdef_apply_tmpl.c:211-235,252-280`). The snapshot producer
   implements the same split (`lf_apply_tmpl.c:104-171`). Thus counting
   `cdef_line_buf` alone does not enumerate every boundary snapshot that
   CDEF can read.

Applying the libaom `2W+1` term to dav1d would require a new mapping of
producer/consumer events, deferred-band lifetimes, shared snapshots, and
allowed schedules, followed by a new proof. This audit does not provide
that mapping or proof and makes no cross-codec memory or throughput
ranking. The row-scaled allocation is an implementation observation.

## Illustrative arithmetic, kept outside the proposed paragraph

The following rows assume **non-resizing, 8-bit 4:2:0, and tightly packed
positive coded-picture byte strides**, `s_Y=width`, `s_UV=width/2`.
They are substitutions into `64+8*width*S`, not actual default allocator
strides, observed decoder allocations, or benchmark results. Actual
padding changes the values. They describe only this allocation.

| Assumed coded dimensions | Superblock size | `S` | Assumed strides Y/UV (B) | Analytic request (B) | Analytic KiB |
|---|---:|---:|---:|---:|---:|
| 1920x1080 | 64 | 17 | 1920 / 960 | 261184 | 255.0625 |
| 1920x1080 | 128 | 9 | 1920 / 960 | 138304 | 135.0625 |
| 3840x2160 | 64 | 34 | 3840 / 1920 | 1044544 | 1020.0625 |
| 3840x2160 | 128 | 17 | 3840 / 1920 | 522304 | 510.0625 |

If the extra-copy branch is selected while holding the coded strides
and `S` fixed, its request is `2*A(r=0)-64`, not `2*A(r=0)`.
The examples do not assign a resize configuration or infer its coded
stride from display dimensions. The proposed manuscript insertion uses
only the general formula and its `O(S)` consequence.

## Evidence locations

All links are the old ledger's fixed commit, not moving HEAD. Their
contents were read locally; the links were not fetched in this audit.

| Claim | Local source range | Fixed upstream URL |
|---|---|---|
| Byte strides, branch, exact size and allocation alignment | `dav1d_src_decode.c:2906-2918` | [decode allocation](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/decode.c#L2906-L2918) |
| Views, extra copy, cached allocation fields | `dav1d_src_decode.c:2924-2964` | [buffer views](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/decode.c#L2924-L2964) |
| Separate restoration allocation | `dav1d_src_decode.c:2967-2999` | [LR allocation](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/decode.c#L2967-L2999) |
| Coded versus upscaled picture | `dav1d_src_decode.c:3527-3546` | [coded picture](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/decode.c#L3527-L3546) |
| Height and 64/128 superblock row count | `dav1d_src_decode.c:3559-3567` | [row count](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/decode.c#L3559-L3567) |
| Deblock/copy dependency before CDEF | `dav1d_src_thread_task.c:793-833` | [task dependencies](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/thread_task.c#L793-L833) |
| Copy wrapper and deferred boundary bands | `dav1d_src_recon_tmpl.c:2005-2050` | [CDEF wrapper](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/recon_tmpl.c#L2005-L2050) |
| Two-line backups and byte/pixel units | `dav1d_src_cdef_apply_tmpl.c:118-138` | [backups](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/cdef_apply_tmpl.c#L118-L138) |
| Boundary snapshot selection | `dav1d_src_cdef_apply_tmpl.c:211-280` | [snapshot consumers](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/cdef_apply_tmpl.c#L211-L280) |
| Snapshot creation and resize condition | `dav1d_src_lf_apply_tmpl.c:104-171` | [snapshot producer](https://github.com/videolan/dav1d/blob/9a275d0c9296f2c0ded9d0dd28f99cf22dea2572/src/lf_apply_tmpl.c#L104-L171) |

For the established libaom side, use the manuscript's existing contract
audit in `revision_20260930/audits/contract_and_scope.md` and the pinned
baseline `thread_common.c:1193-1220`, `cdef.c:439-456`. The current audit
does not refresh or independently recertify that theorem.

## Deliverables and reproduction

- `insertion_en.tex`: proposed 86-word English paragraph, counting each
  inline formula as one token and excluding its citation command. It is
  a suggested insertion, and no manuscript file was changed.
- `verify_formula.py`: standard-library Python script; checks all eight
  old source hashes, the fixed `decode.c` hash, literal source formulas,
  height rounding, allocation algebra, signed strides, and region totals.
- `verification.json`: generated report; 262144 height/flag checks and
  2016 allocation/branch/stride combinations passed.
- `analytic_examples.csv`: the four explicitly assumed arithmetic cases.
- `audit_execution.json`: audit provenance and output hashes.

From the workspace root, run:

```sh
python3 CDEF_paper_pipeline/revision_20261001/dav1d/verify_formula.py
```

The script reads the fixed local snapshots and writes only
`verification.json` and `analytic_examples.csv` beside itself. It does
not compile or run dav1d. The checks verify integer algebra in a valid
dimension domain and do not audit machine-integer overflow or exhaustive
runtime/error-path behavior.
