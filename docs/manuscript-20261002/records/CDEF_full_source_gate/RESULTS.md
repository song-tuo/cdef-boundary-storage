# CDEF full-source gate：PASS_TO_PAPER_OUTLINE

本次限定范围内的工程门禁通过；本任务没有开始论文或提纲写作。

本报告仅汇总新的源码实验，不把交接包的 archive 原型结果合并为本次证据。三份 Priority-0 前作核查按用户指令保持关闭，未继续检索。

## 源码与三变体

- 已取得完整、可写的 Debian `aom 3.12.1-1` 源码。两个源码包文件 SHA-256 与 `.dsc` 一致。
- 官方 `v3.12.1` 提交：`10aece4157eb79315da205f39e19bf6ab3ee30d0`；Git tree：`f401599b7be4c53cbcc2735969a4970c744dd372`。Debian orig 的 1,347 个对应文件全部与官方 Git blob 一致，无缺失或内容差异。
- `baseline`、`type_fix`、`token` 各有独立源码树、构建目录、库和可执行文件。baseline manifest 复核一致；type_fix 仅改一处 sizeof；token 增量只涉及 3 个源文件，+115/-12 行。
- 主配置统一为 Release，编码器/解码器/高位深均启用，`CONFIG_LIBYUV=0`、`CONFIG_WEBM_IO=0`。Debug、ASan+UBSan、TSan 均从完整源码重建；286 个 libaom archive 成员全部有对应插桩编译命令。
- 平台：macOS 26.6.2，Apple M5 Pro，18 核，48 GiB，Apple Clang 21.0.0，CMake 4.4.2。完整身份、参数及散列见 `source_identity.json` 和 `results/instrumentation_audit.json`。

## 正确性与安全性

| 检查 | 结果 |
|---|---|
| 三变体配对可见像素 SHA-256 与帧数 | 540 次通过 |
| token Debug / ASan+UBSan / TSan 配对矩阵 | 各 180 次通过 |
| 无效和截断输入，三 release 变体及两种 sanitizer | 750 次一致 |
| 三变体上游 CDEF/common/decoder API | 各 208 项通过 |
| 三变体 release conformance / 两种 sanitizer conformance | 各 3,899 项通过 |
| token tile、row-MT 相关用例 | 508 个唯一用例最终通过 |
| token resize、superres、frame-size、error resilience | 386 项通过 |
| frame-parallel 专用配置 | 45 项通过，含全部 42 个 Large 用例 |
| 上游 shell decoder 测试 | 三变体均通过 |
| 两个官方 MKV resize 码流补验 | 100 次逐帧 MD5 符合官方值 |
| 源码故障及负对照 | ASan+UBSan、TSan 各 156 次通过，各有 156 次后续干净解码 |
| 同一 codec 实例出错后重新解码关键帧 | 两种 sanitizer 各 99 次通过 |
| 系统 leaks 正常/故障销毁检查 | 36 次无泄漏；故意丢失分配的探针检出 32,768 字节 |

配对矩阵覆盖 8/10/12-bit、mono/4:2:0/4:2:2/4:4:4、奇数尺寸、部分末行、单行/边缘尺寸、tiles、线程 1/2/4/8/16、row-MT off/on、编码的 frame-parallel 标记。故障包括冻结的五阶段、完整复制前/部分复制后、各平面 line buffer 分配以及 owner metadata 分配。

macOS ASan 不支持 LeakSanitizer，已保存实际探测日志；泄漏检查采用系统 leaks。声明的 sanitizer 结果限于实际执行路径。未把中断的、未优化的广泛编码压力套件算作通过。上游自带的 3 个 DISABLED resize speed 用例保持禁用；当前 CPU 不支持的 SVE 系列由上游框架排除。

## 冻结内存结果

| 4K、4:2:0，三个内容家族均一致 | boundary requested bytes | 相对 type_fix |
|---|---:|---:|
| baseline | 8,355,840 | 分开记录 sizeof 效应 |
| type_fix | 2,088,960 | 基准 |
| token，实际 W=8 | 522,240 | 减少 75.00% |
| token，实际 W=16 | 1,013,760 | 减少 51.47% |

额外的 token 逻辑元数据在 R=34 时为 W=8 的 356 字节、W=16 的 420 字节（未含该元数据 allocator padding）。1080p、R=17、W=16 属于 R 接近 W 的情况，边界请求字节仅减少 5.88%；收益明确依赖目标工况。

usable bytes 使用 libaom 对齐头指向的实际 malloc block 调用 malloc_size；进程峰值 RSS 使用 macOS getrusage，单位为字节。CDEF 阶段时间及行同步等待在独立 audit 构建记录；行同步等待不包括其他 codec 锁。池无容量等待路径，pool wait count 的零值是结构性结果。主要确认性计时使用没有这些日志插桩的 release 构建。完整结果在 `memory/memory_results.csv`，原始逐帧日志保留。

## 冻结计时与灵敏度

- 协议 SHA-256：`e2a0c24d302119a7f69b37b2e23f386e84e5dcb0ef72551bb5336ff2ae5f0cb8`。确认前锁定可执行文件、输入、主比较、阈值和随机种子。
- 主比较为 token/type_fix；3 个固定合成内容家族 × 1080p/4K × 线程 2/8/16，共 18 个单元。每单元 1 个预热 pair、12 个 AB/BA 平衡 pair。
- 主指标为 aom_codec_decode 调用及 flush 的累计单调时钟时间；预加载输入和可见像素哈希不计入该指标。每个过程的 RSS、时间、帧数、哈希和主机负载均保留。
- 不劣阈值固定为 1.02；对 12 个配对比值的中位数做固定种子的 50,000 次 percentile bootstrap。上界 ≤1.02 才通过；下界 >1.02 触发实质减速停止；其余为无法确证不劣。未删除离群值或追加重复。
- 延迟对照使用同一 harness 和同一时间区域，每输入包注入 82 ms；剂量在确认前校准。6 个对照单元各 12 个 pair，检出阈值、剂量核算和身份检查均按冻结规则判定。该大剂量对照不单独证明 2% 效应的检测能力。

| 主比较单元 | W | token/type_fix 中位数 | 95% CI | 冻结判定 |
|---|---:|---:|---|---|
| timing_waves_1920x1080 | 2 | 0.9981 | [0.9941, 1.0040] | PASS |
| timing_waves_1920x1080 | 8 | 0.9987 | [0.9899, 1.0068] | PASS |
| timing_waves_1920x1080 | 16 | 1.0012 | [0.9969, 1.0063] | PASS |
| timing_waves_3840x2160 | 2 | 0.9961 | [0.9871, 1.0040] | PASS |
| timing_waves_3840x2160 | 8 | 1.0025 | [0.9959, 1.0074] | PASS |
| timing_waves_3840x2160 | 16 | 0.9980 | [0.9953, 1.0030] | PASS |
| timing_checker_1920x1080 | 2 | 1.0029 | [0.9858, 1.0063] | PASS |
| timing_checker_1920x1080 | 8 | 1.0011 | [0.9944, 1.0114] | PASS |
| timing_checker_1920x1080 | 16 | 1.0026 | [0.9632, 1.0121] | PASS |
| timing_checker_3840x2160 | 2 | 0.9969 | [0.9925, 1.0074] | PASS |
| timing_checker_3840x2160 | 8 | 0.9820 | [0.9625, 1.0077] | PASS |
| timing_checker_3840x2160 | 16 | 1.0024 | [0.9882, 1.0150] | PASS |
| timing_texture_1920x1080 | 2 | 0.9971 | [0.9809, 1.0054] | PASS |
| timing_texture_1920x1080 | 8 | 0.9884 | [0.9763, 1.0011] | PASS |
| timing_texture_1920x1080 | 16 | 1.0045 | [0.9709, 1.0179] | PASS |
| timing_texture_3840x2160 | 2 | 1.0036 | [1.0003, 1.0138] | PASS |
| timing_texture_3840x2160 | 8 | 1.0048 | [0.9792, 1.0154] | PASS |
| timing_texture_3840x2160 | 16 | 1.0006 | [0.9943, 1.0066] | PASS |

灵敏度通过：6/6。最终状态：**PASS_TO_PAPER_OUTLINE**。

## 可维护性、失败记录与范围

动态所有权直接放入现有同步结构，沿用原有任务锁、行条件变量、错误唤醒和销毁路径。没有外部状态表、ABI 偏移或符号替换。消费行在过滤结束后才释放 incoming-top/own-bottom；不释放由下游消费的 outgoing-top。独立有限调度模型检查了 3,932 个状态，并给出固定 row-modulo ring 的合法别名反例。详见 `maintainability/review.md`。这是工程自审，不代表上游维护者已接受。

保留的早期失败包括：Debian 镜像缺失 revision tar 后改用官方 snapshot；测试数据临时 TLS 失败及重试；aomenc 对非 4:2:0 的显式 12-bit profile 在初始化前设置 control 导致输入准备失败，改用原有自动 profile 升级且验证实际解码位深/抽样；数据未就绪时 80 个上游用例失败，校验完成后全部补跑通过；tarball 的 shell 测试误用 git describe，使用仅影响版本探测的 no-git shim；不可用的 LSan，以及没有有效诊断输出的早期 leaks 启动方式。以上都未删除或计入最终通过数。

现有证据覆盖本机和记录的码流/调度/故障范围；不声称所有架构、所有合法 AV1 输入或所有未来调度均经过穷尽运行。RSS 及软件分配不作为硬件面积、功率或能量证据。全库插桩和原型 archive 的证据层级保持分离。

**没有开始论文写作，也没有生成论文提纲。**
