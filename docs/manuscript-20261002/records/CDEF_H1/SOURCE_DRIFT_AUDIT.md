# Source drift audit

Official source: https://aomedia.googlesource.com/aom . Git fetches, commit identities, full archive exports and independently recomputed Git blob identities are in logs/003–006 and results/source_identity.json. Current main is pinned at audit time, not a moving claim.

## Finding

None of the three revisions implements equivalent worker-bounded pre-filter boundary storage. All retain frame-row-indexed MT line buffers. Stage 0 does not stop H1.

For all three revisions: R = ceil(mi_rows/MI_SIZE_64X64); the decoder passes its allocated CDEF worker count (num_workers, W), not the instantaneous number of busy workers. The existing job mutex issues monotonically increasing row jobs. A row copies its outgoing top boundary and its own bottom boundary, signals that copy completion, waits for the preceding row copy, then filters in place. The predecessor copy is what preserves the consumer's pre-filter pixels.

Upstream MT allocation per plane is sizeof(*cdef_info->linebuf) × R × (CDEF_VBORDER << 1) × stride. Because linebuf is an array of pointers, this sizeof is pointer width, not sample width. The frozen type_fix changes this single sample-size expression to sizeof(**cdef_info->linebuf); the storage remains row-indexed. Upstream top addressing is row × border × stride; bottom base is R × border × stride and bottom row addressing is likewise row-indexed.

W=1 uses the unchanged serial ping-pong path. Its legacy allocation is outside the H1 tight MT capacity acceptance, as explicitly confirmed by the user. The encoder uses the same common CDEF synchronization/worker structures, so its frame-parallel path requires an independent hybrid safety check.

## Source evidence (line numbers refer to exported files)

### v3.12.1 — 10aece4157eb79315da205f39e19bf6ab3ee30d0

| Source | Git blob | SHA-256 |
|---|---|---|
| av1/common/alloccommon.c | 38b9e6464bcd890287cd08f0c1b49024f874f4c6 | f4a65a29fa87fab19691152ec30a4ff9bcc0ca348a858e97e1837da7c5f9e043 |
| av1/common/thread_common.c | 0ff6238992c616efd412089ddf620fdf11dbd2e6 | 960bd4bfd41383d522e4fb655ba495eeb2014d0f8e58edb341ee83d8d3722bcc |
| av1/common/thread_common.h | 1f2557a7851cf5a1d62dd1a6ee818c2941e263ff | 96bc6e215d8ebf36a9c8fbae0852e932727b126a1bfc4fd19ea3fd6558c973d0 |
| av1/common/cdef.c | c39fca30837ddfd93bbf1a8ff66bf5b001f7c334 | a2832163c6041efb3085b8322b55b3d531a69a4641db14bdb4a6e01189c2fb3f |
| av1/common/cdef.h | c7a8a331cfbd5e30129bdfb99072dc59c07fca61 | 8fbe20aed8ba8d608de1caa38fa8ac274c640a7def521602a93e2a7080b5d0b1 |
| av1/decoder/decodeframe.c | cbf5e9121a33e0da137772233f6d34476f103f4e | 6737baaec53f6b2406a190a35ca5766baad4151979f1fbd99a66441b551c5519 |
| av1/decoder/decoder.c | 0ae0b86dbf2a32ab82c5ec820378adce2ad708ff | a056099000152da6c52f57c00c7960c2e14b21328ee37cc36256aba7bd44f45a |
| av1/encoder/ethread.c | fcffd7af7088fcccfc72f36e6d1b7fd950638d94 | 91546100e800e26632877f8d8f3e36cbef00f295d650068442653006eb0592ad |
| av1/encoder/encoder.c | 87f25157f1d2d0d67a547ab3c60fd8dc1901700b | 338301d5ffe7b1f6e44fa49cb76c853dda8c631bc3d3d6f0ab0d2d407b4ac67a |

Relevant anchors:
- `v3.12.1/av1/common/alloccommon.c:225`: `new_linebuf_size[plane] = sizeof(*cdef_info->linebuf) * num_bufs *`
- `v3.12.1/av1/common/thread_common.c:1075`: `for (int fbr = 0; fbr < nvfb; fbr++) cdef_row_mt_sync_write(cdef_sync, fbr);`
- `v3.12.1/av1/common/thread_common.c:1195`: `uint16_t *top_linebuf = &linebuf[plane][0];`
- `v3.12.1/av1/common/thread_common.c:1196`: `uint16_t *bot_linebuf = &linebuf[plane][nvfb * CDEF_VBORDER * stride];`
- `v3.12.1/av1/common/thread_common.c:1219`: `cdef_row_mt_sync_write(cdef_sync, fbr);`
- `v3.12.1/av1/common/thread_common.c:1220`: `cdef_row_mt_sync_read(cdef_sync, fbr);`
- `v3.12.1/av1/common/thread_common.c:1231`: `void av1_cdef_frame_mt(AV1_COMMON *const cm, MACROBLOCKD *const xd,`
- `v3.12.1/av1/decoder/decodeframe.c:5339`: `av1_cdef_frame_mt(cm, &pbi->dcb.xd, pbi->cdef_worker,`

### v3.15.1 — 44d0a57786f432d933ff64b653347c66f4d0fa1d

| Source | Git blob | SHA-256 |
|---|---|---|
| av1/common/alloccommon.c | 38b9e6464bcd890287cd08f0c1b49024f874f4c6 | f4a65a29fa87fab19691152ec30a4ff9bcc0ca348a858e97e1837da7c5f9e043 |
| av1/common/thread_common.c | dee45b44c2def5ec01cb8a20f3e103d15a51770f | b05274b70a61e2b5a136800848986c2419e9372777384c5b6a0b285f725d51bc |
| av1/common/thread_common.h | 5d467c5d00b4c3d93e2438e7c68c15d5b90763b9 | 02063f362089a24988565088e79642ca75fc558bedd3e2081560c1713d7f81c8 |
| av1/common/cdef.c | c39fca30837ddfd93bbf1a8ff66bf5b001f7c334 | a2832163c6041efb3085b8322b55b3d531a69a4641db14bdb4a6e01189c2fb3f |
| av1/common/cdef.h | 859bb1a2f31788918b19bd59b0c030e9f058c8be | 184f1fa87456998406b4dbbfb135f00dec9ccd96ddf5be8fb69db1ef03589301 |
| av1/decoder/decodeframe.c | b6ee3ace02b21f035beb34f972d09a66293c6022 | 20fab5708fda23a434a5bfc79179d6561eb6325524673c6faa9425e6f8412bf6 |
| av1/decoder/decoder.c | 81a88b403e5e96758022dcab0301ba613aeb65ff | 5210a92697e693a13dda032c1f054a0db8c32b3dd86995a0bed220fe75b7c89f |
| av1/encoder/ethread.c | d46b3ee1a7179ed7a4fe7928b141ee1eb609bb4a | c4ffad3e10876a1a66cbe485a1abb2acce2eeb1360bc877fe46e9a6faf53491e |
| av1/encoder/encoder.c | 38421900967ee53d05ea5aeb6d459841839030e2 | ff110fc306f9db3b0f662768fcebd924020ff7d919a824f238d9b7c0983b892a |

Relevant anchors:
- `v3.15.1/av1/common/alloccommon.c:225`: `new_linebuf_size[plane] = sizeof(*cdef_info->linebuf) * num_bufs *`
- `v3.15.1/av1/common/thread_common.c:1077`: `for (int fbr = 0; fbr < nvfb; fbr++) cdef_row_mt_sync_write(cdef_sync, fbr);`
- `v3.15.1/av1/common/thread_common.c:1197`: `uint16_t *top_linebuf = &linebuf[plane][0];`
- `v3.15.1/av1/common/thread_common.c:1198`: `uint16_t *bot_linebuf = &linebuf[plane][nvfb * CDEF_VBORDER * stride];`
- `v3.15.1/av1/common/thread_common.c:1221`: `cdef_row_mt_sync_write(cdef_sync, fbr);`
- `v3.15.1/av1/common/thread_common.c:1222`: `cdef_row_mt_sync_read(cdef_sync, fbr);`
- `v3.15.1/av1/common/thread_common.c:1233`: `void av1_cdef_frame_mt(AV1_COMMON *const cm, MACROBLOCKD *const xd,`
- `v3.15.1/av1/decoder/decodeframe.c:5441`: `av1_cdef_frame_mt(cm, &pbi->dcb.xd, pbi->cdef_worker,`

### main — ae410fe8b7bd45f3cf61dc8f112dc783e2a08089

| Source | Git blob | SHA-256 |
|---|---|---|
| av1/common/alloccommon.c | 38b9e6464bcd890287cd08f0c1b49024f874f4c6 | f4a65a29fa87fab19691152ec30a4ff9bcc0ca348a858e97e1837da7c5f9e043 |
| av1/common/thread_common.c | dee45b44c2def5ec01cb8a20f3e103d15a51770f | b05274b70a61e2b5a136800848986c2419e9372777384c5b6a0b285f725d51bc |
| av1/common/thread_common.h | 5d467c5d00b4c3d93e2438e7c68c15d5b90763b9 | 02063f362089a24988565088e79642ca75fc558bedd3e2081560c1713d7f81c8 |
| av1/common/cdef.c | c39fca30837ddfd93bbf1a8ff66bf5b001f7c334 | a2832163c6041efb3085b8322b55b3d531a69a4641db14bdb4a6e01189c2fb3f |
| av1/common/cdef.h | 859bb1a2f31788918b19bd59b0c030e9f058c8be | 184f1fa87456998406b4dbbfb135f00dec9ccd96ddf5be8fb69db1ef03589301 |
| av1/decoder/decodeframe.c | fcb328de403254d28dad6e1037111921d0c281ee | 45ad99f27edae6b161b43c404b0549f6b64939a0d08f7a60963e0938ea0f5b49 |
| av1/decoder/decoder.c | 81a88b403e5e96758022dcab0301ba613aeb65ff | 5210a92697e693a13dda032c1f054a0db8c32b3dd86995a0bed220fe75b7c89f |
| av1/encoder/ethread.c | 581294c01cb64762f192b8d3bd46bfbdab5a4840 | 634e9595889777e78f9e3380ef98cd9d3fcb30ec8f39d36dd5daab58d240beb2 |
| av1/encoder/encoder.c | 359c5294ba5ba8adcdafbcb5e552761c5701c29a | 07c41ec3fd7f5b9af0153af3e3840d8fb4ccb785e07d79b4b65ccb7cc75205ea |

Relevant anchors:
- `main/av1/common/alloccommon.c:225`: `new_linebuf_size[plane] = sizeof(*cdef_info->linebuf) * num_bufs *`
- `main/av1/common/thread_common.c:1077`: `for (int fbr = 0; fbr < nvfb; fbr++) cdef_row_mt_sync_write(cdef_sync, fbr);`
- `main/av1/common/thread_common.c:1197`: `uint16_t *top_linebuf = &linebuf[plane][0];`
- `main/av1/common/thread_common.c:1198`: `uint16_t *bot_linebuf = &linebuf[plane][nvfb * CDEF_VBORDER * stride];`
- `main/av1/common/thread_common.c:1221`: `cdef_row_mt_sync_write(cdef_sync, fbr);`
- `main/av1/common/thread_common.c:1222`: `cdef_row_mt_sync_read(cdef_sync, fbr);`
- `main/av1/common/thread_common.c:1233`: `void av1_cdef_frame_mt(AV1_COMMON *const cm, MACROBLOCKD *const xd,`
- `main/av1/decoder/decodeframe.c:5446`: `av1_cdef_frame_mt(cm, &pbi->dcb.xd, pbi->cdef_worker,`

