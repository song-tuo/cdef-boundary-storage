# Existing resource accounts

All values below are direct selections from existing records; no new resource run or statistical estimate is introduced. RESOURCE_ACCOUNTING.csv is the unchanged 27-row H1 allocation table. HISTORICAL_PROCESS_MEMORY.csv is the unchanged 90-row full-source memory table.

## H1, 3840 x 2160, eight workers (bytes)

| Recorded category | type_fix | owner pools | hybrid |
|---|---:|---:|---:|
| Pixel requested | 2,088,960 | 522,240 | 522,240 |
| Pixel usable | 2,097,152 | 524,288 | 524,288 |
| Owner requested | 0 | 68 | 36 |
| Owner usable | 0 | 96 | 64 |
| Row structure requested | 816 | 1,088 | 1,088 |
| Row structure usable | 896 | 1,280 | 1,280 |
| Row-index metadata within row structure | 0 | 272 | 272 |
| Worker structure requested | 3,904 | 3,904 | 3,968 |
| Worker structure usable | 4,096 | 4,096 | 4,096 |
| Sync structure sizeof | 32 | 48 | 48 |
| Padding in charged allocation categories | 8,464 | 2,460 | 2,396 |

Selectors: width=3840, height=2160, W_requested=8; variants type_fix/dual_token/hybrid. `command_log` links the accounting commands. Row-index metadata is already contained in row-structure bytes; adding it again would double count. Sync sizeof is a structure-layout measurement, not a standalone allocator request. Padding is already represented by requested versus usable sizes. Thus these overlapping categories must not be summed indiscriminately into a claimed whole-decoder total.

## Historical process memory

The full-source memory CSV records `peak_rss_bytes` from macOS `getrusage(RUSAGE_SELF)` for each standalone harness process. It includes input/harness allocations, decoder/frame storage and other process memory. `stage_ns` is an instrumented CDEF-stage observation from that run, not H1's clean decode-plus-flush timing endpoint.

These historical processes are separate from H1 accounting and H1 balanced timing blocks. Their raw RSS, stage time, hashes and frame counts are retained together in the original rows. They are not joined to H1 metadata to construct a synthetic system-benefit row. This revision reports no new process-memory percentage, net decoder footprint or timing inference. The paper's numerical resource claim remains boundary allocation.

## Timing cost

The recorded H1 timing summaries and all block ratios are supplied separately. Every owner-pool/reference interval includes one. These intervals leave the runtime cost imprecisely estimated; they do not establish zero overhead. The original primary hybrid/reference result stays six passes and twelve inconclusive cells at 1.02.
