# CDEF line-buffer allocation uses sizeof(pointer) instead of sizeof(uint16_t)

In `av1_alloc_cdef_buffers()`, the allocation size for CDEF top/bottom line buffers uses `sizeof(*cdef_info->linebuf)`. The member is declared `uint16_t *linebuf[MAX_MB_PLANE]`, so this operand has pointer type. On the tested 64-bit platform it is 8 bytes, whereas each stored sample is 2 bytes. This requests four times the intended line-buffer storage.

## Affected source snapshots

- libaom v3.15.1, commit `44d0a57786f432d933ff64b653347c66f4d0fa1d`.
- main snapshot retrieved September 30, 2026, commit `9f9c3f7475793f1a80fc8fb811dbff84549a91df`.
- Current main checked October 1, 2026, commit `ae410fe8b7bd45f3cf61dc8f112dc783e2a08089`; the two relevant files are byte-identical to the tested September 30 snapshot.
- The earlier v3.12.1 source used in the associated experiment also contains the expression.

Source links:

- [Allocation expression, pinned main](https://aomedia.googlesource.com/aom/+/ae410fe8b7bd45f3cf61dc8f112dc783e2a08089/av1/common/alloccommon.c#225)
- [CdefInfo declaration, pinned main](https://aomedia.googlesource.com/aom/+/ae410fe8b7bd45f3cf61dc8f112dc783e2a08089/av1/common/av1_common_int.h#207)

## Minimal reproduction

The attached `sizeof-reproducer.c` extracts the relevant declaration and expression, and can be run with:

```sh
cc -std=c11 -Wall -Wextra -pedantic sizeof-reproducer.c -o sizeof-reproducer
./sizeof-reproducer
```

This demonstrates the C operand-size calculation; it does not execute a decoder. On the tested arm64 system it prints operand sizes 8 and 2, and requested-byte totals 8,355,840 and 2,088,960 for 3840x2160 4:2:0 with 34 frame rows. The full-library allocation diagnostics independently recorded these same totals at 8 and 16 workers on both listed snapshots.

## Proposed fix

Use the sample element size:

```diff
-      new_linebuf_size[plane] = sizeof(*cdef_info->linebuf) * num_bufs *
+      new_linebuf_size[plane] = sizeof(**cdef_info->linebuf) * num_bufs *
```

An equivalent spelling is `sizeof(*cdef_info->linebuf[plane])`. The attached patch changes only the sizeof operand. It retains the existing buffer count, layout and synchronization.

## Validation already performed

On Apple M5 Pro / arm64 macOS 26.6.2 with Apple clang 21.0.0, baseline and type-fix were built independently from v3.15.1 and the September 30 main snapshot. The October 1 check compared the relevant source files; it was not a new full build or test campaign. Each of those four release builds passed 38 decode smoke cases (19 inputs at 8/16 workers) and 242 upstream `AV1/TestVectorTest.MD5Match/*` cases. The smoke checks matched the retained v3.12.1 baseline decoded pixels and frame counts. Separate full-library diagnostic builds confirmed the requested-byte calculation above.

The reported issue is excess allocation. These checks found matching decoded output after the type-size fix. This report concerns the isolated type fix; worker-bounded buffer reuse is a separate change.

## Related upstream change checked

Gerrit [176844](https://aomedia-review.googlesource.com/c/aom/+/176844) and its cherry-picks [176921](https://aomedia-review.googlesource.com/c/aom/+/176921) and [178203](https://aomedia-review.googlesource.com/c/aom/+/178203), titled `cdef_alloc_data: fix sizeof in allocation`, repaired encoder `sb_index` in `av1/encoder/pickcdef.c` in 2023 (aomedia:3454). This report concerns `linebuf` in `av1/common/alloccommon.c`, whose pointer-sized operand remains in the pinned current source. The older issue number is not a report number for this finding.
