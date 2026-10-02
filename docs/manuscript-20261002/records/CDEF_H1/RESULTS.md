# CDEF-H1 决策报告

最终状态：**KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT**

KEEP 由事前冻结的计时确认门触发：6/18 个 cell 通过 1.02 非劣 margin，12 个区间仍不确定，明确性能退化为 0 个。Hybrid 已达到有限帧 strip 容量界，并通过本轮实际执行的语义与安全检查；本轮不据此升级论文主实现。

本轮只执行 CDEF-H1；旧 CDEF、U、AL 结果未覆盖，U 和 AL 不恢复。W=1 按用户确认保留串行路径，只验证兼容性。

## 门禁与证据

- Source drift：v3.12.1、v3.15.1 与固定 main `ae410fe8b7bd45f3cf61dc8f112dc783e2a08089` 均保留 frame-row-indexed 边界存储，没有等价解决；27 个相关 Git blob 已校验。
- 精确语义：432 个配置 × 三实现 × clean/audit，共 2592 条记录；失败 0。覆盖高位深、420/444、row-MT 开关、W/R 边界、CDEF 开关和同实例尺寸增减。
- hybrid 独立 Debug/ASan+UBSan/TSan：1296 条，失败 0。五个 Debug/sanitizer 库各 286 个成员核对编译参数。
- 注入与恢复：1260 条，失败 0；完整错误与预期非零退出码保留。
- 官方 MKV resize：64 次逐帧 MD5 比对；native leaks：36 次，失败 0。沙箱内 task-port 失败另列，不计 PASS。
- Encoder frame-parallel：45 项独立 Release 测试，并补验 ASan+UBSan / TSan 各三个固定小用例；状态见 safety_matrix.csv。

| 上游选择组 | 测试记录 |
|---|---:|
| release/core | 208 |
| debug/core | 208 |
| asan/core | 208 |
| tsan/core | 208 |
| release/conformance | 3899 |
| asan/conformance | 3899 |
| tsan/conformance | 3899 |
| release/row_tiles | 508 |
| release/resize_error | 389 |

三个 resize 分片的原始汇总标为 INCOMPLETE，是因为每个 XML 列出一个上游默认禁用的 DISABLED_Speed 用例。逐项表将其记为 DISABLED_NOT_EXECUTED，不计入执行 PASS；受支持且实际选择执行的 correctness 用例另行验收。所有 skipped/unsupported、禁用测试和失败日志均单独保留；不把架构不支持的 SVE 路径算作通过。上游 WebM CLI 在该构建中关闭，两个原有 MKV resize 内容由原始 AV1 payload 加官方逐帧 MD5 独立补验。

## 容量与实现复杂度

27 条分辨率/worker/实现记录测量实际 requested 与 backing-block usable bytes。Hybrid 的 MT strip 数精确等于 min(2R−2,2W+1)，bottom owner 数组、free-slot scan、capacity wait 均不存在。每行地址索引仍保留，并单独计入；原有同步元数据仍随 R 变化，因此不把整个解码器内存说成仅随 W 变化。

4K、W=8：type_fix 像素边界请求 2,088,960 B；dual_token 与 hybrid 均为 522,240 B，减少 75%。Hybrid owner 请求从 68 B 降到 36 B，但 worker 结构从 3,904 B 增到 3,968 B；删除 owner 状态不意味着总元数据更小。所有 allocator padding 单列。这些不是 RSS、SRAM、area、power 或 energy。

## 新 block 计时

每个 cell 为 12 个完整三实现 block；六种顺序各两次。置信区间重采样单位只有 block，50,000 次，所有 648 次测量保留，没有邻接 pair 独立样本假设、旧 token CI、离群值删除或结果后追加。仅支持冻结本机 workload 下的结论。主要比较 hybrid/type_fix；次要 dual_token/hybrid 见 timing_summary.csv。

| workload | resolution | W | hybrid/type_fix 中位数 | 95% CI | 判定 |
|---|---|---:|---:|---|---|
| waves | 1920×1080 | 2 | 1.0138 | [0.8743, 1.0897] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| waves | 1920×1080 | 8 | 1.0011 | [0.8710, 1.2142] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| waves | 1920×1080 | 16 | 1.0012 | [0.8277, 1.2202] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| waves | 3840×2160 | 2 | 0.9992 | [0.9739, 1.0457] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| waves | 3840×2160 | 8 | 0.9952 | [0.9430, 1.0419] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| waves | 3840×2160 | 16 | 0.9937 | [0.9344, 1.0715] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| checker | 1920×1080 | 2 | 0.9997 | [0.9681, 1.0387] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| checker | 1920×1080 | 8 | 1.0046 | [0.9781, 1.0440] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| checker | 1920×1080 | 16 | 1.0048 | [0.9681, 1.0430] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| checker | 3840×2160 | 2 | 1.0011 | [0.9958, 1.0119] | PASS_LOCAL_NONINFERIORITY |
| checker | 3840×2160 | 8 | 1.0007 | [0.9928, 1.0127] | PASS_LOCAL_NONINFERIORITY |
| checker | 3840×2160 | 16 | 1.0051 | [0.9957, 1.0148] | PASS_LOCAL_NONINFERIORITY |
| texture | 1920×1080 | 2 | 1.0071 | [0.9748, 1.0328] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| texture | 1920×1080 | 8 | 1.0074 | [0.9715, 1.0416] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| texture | 1920×1080 | 16 | 1.0065 | [0.9798, 1.0393] | INCONCLUSIVE_LOCAL_NONINFERIORITY |
| texture | 3840×2160 | 2 | 1.0047 | [0.9950, 1.0103] | PASS_LOCAL_NONINFERIORITY |
| texture | 3840×2160 | 8 | 1.0030 | [0.9943, 1.0104] | PASS_LOCAL_NONINFERIORITY |
| texture | 3840×2160 | 16 | 1.0044 | [0.9974, 1.0108] | PASS_LOCAL_NONINFERIORITY |

1.02 是事前冻结的本机非劣 margin；区间越过它不能记为已证实非劣。不作 universal ≤2% overhead 或 speedup 声明。

## 固定真实内容

三个官方源的 ID、SHA-256 和三档编码设置均在解码和计时前冻结。所有 9 个码流 × W=2/8/16 × 三实现共 81 条均保留。真实内容无需依据 timing 替换。下表为 W=8 hybrid 的实际非零强度 luma 8×8 块占可见块比例；0 强度方向计算单独计数，避免把方向计算等同像素滤波。低/中/高仅指这些固定内容内观测到的活动范围，不是总体内容分类。

| 内容 | q0 | q24 | q56 |
|---|---:|---:|---:|
| real_park_joy_90p_8_420 | 0.00% | 47.96% | 67.42% |
| real_crowd_run_360p_10_150f | 0.00% | 48.93% | 62.86% |
| real_wikipedia_420_360p_60f | 0.00% | 25.42% | 35.70% |

## 保留与限制

主协议、实现 seal、输入 hash、源码、patch、全部实验 stdout/stderr/退出码均保留。source preparation 和诊断头文件的编译错误发生于第一轮科学解码前，未改科研设置。详细归因见 PATCH_LEDGER.md。

本轮决定理由：prospective_local_block_noninferiority_not_established_in_all_18_cells.

只有 PROCEED 才把 hybrid 定为新论文主实现，并将 dual-token 降为探索/对照；本轮始终不覆盖旧论文文件。未通过时不作该提升，也不修改实现、门槛或输入来补救本轮。
