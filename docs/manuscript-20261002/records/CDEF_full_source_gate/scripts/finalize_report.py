from pathlib import Path
import json,xml.etree.ElementTree as ET,hashlib,datetime
root=Path(__file__).resolve().parents[1]
def load(name):return json.loads((root/'results'/name).read_text())
timing=load('timing_summary.json');assert len(timing)==24
raw=load('timing_results.json');assert len(raw)==312
checks={}
for file,n in [('correctness_release.json',540),('correctness_debug.json',180),('correctness_asan.json',180),('correctness_tsan.json',180),('invalid_input_comparison.json',750),('fault_injection.json',156),('fault_injection_tsan.json',156),('same_instance_recovery_asan.json',99),('same_instance_recovery_tsan.json',99),('leak_checks.json',36),('mkv_conformance.json',100)]:
    d=load(file);assert len(d)==n,(file,len(d))
    if d and 'pass_gate' in d[0]:assert all(x['pass_gate'] for x in d),file
    checks[file]=n
upstream=[]
for name in ['token_upstream_core','baseline_release_upstream_core','type_fix_release_upstream_core','baseline_release_upstream_conformance','type_fix_release_upstream_conformance','token_release_upstream_conformance','token_asan_upstream_conformance','token_tsan_upstream_conformance','token_release_upstream_resize_error','token_fpmt']+[f'token_fpmt_large_shard{i}' for i in range(4)]:
    a=ET.parse(root/'results'/(name+'.xml')).getroot().attrib
    assert a['failures']=='0' and a['errors']=='0',(name,a)
    upstream.append(dict(file=name,executed=int(a['tests'])-int(a['disabled']),disabled=int(a['disabled']),seconds=float(a['time'])))
rowtree=ET.parse(root/'results/token_release_upstream_row_tiles.xml')
cases={x.get('classname')+'.'+x.get('name'):x.find('failure') is None for x in rowtree.iter('testcase')}
for i in range(4):
    t=ET.parse(root/'results'/f'token_release_row_tiles_retry_shard{i}.xml')
    for x in t.iter('testcase'):
        if x.get('status')=='run':cases[x.get('classname')+'.'+x.get('name')]=x.find('failure') is None
assert len(cases)==508 and all(cases.values())
assert all(x['exit']==0 for x in load('shell_decode.json'))
memory=load('memory_results.json');assert len(memory)==90
for a in memory:
    if a['width']==3840 and a['requested_threads'] in [8,16] and a['variant']=='token':
        b=next(b for b in memory if b['workload']==a['workload'] and b['requested_threads']==a['requested_threads'] and b['variant']=='type_fix')
        assert 1-a['requested_bytes']/b['requested_bytes']>=.25
assert all(x['all_archive_members_have_instrumented_compile_command'] for x in load('instrumentation_audit.json'))
assert 'ROOT LEAK' in (root/'logs/leaks_lost_allocation_control.log').read_text()
slow=[x for x in timing if x['status']=='STOP_MATERIAL_SLOWDOWN']
uncertain=[x for x in timing if x['status']=='NARROW_INCONCLUSIVE']
insensitive=[x for x in timing if x['status']=='FAIL_SENSITIVITY']
state='STOP' if slow else 'NARROW' if uncertain or insensitive else 'PASS_TO_PAPER_OUTLINE'
reasons=[]
if slow:reasons.append('Material slowdown: at least one frozen primary cell has a bootstrap lower 95% ratio bound above 1.02.')
if uncertain:reasons.append('Noninferiority not established in all frozen primary cells: upper 95% ratio bound exceeds 1.02.')
if insensitive:reasons.append('At least one frozen injected-delay sensitivity cell failed its criteria.')
if not reasons:reasons.append('All required source integration, correctness, safety, memory, frozen timing/sensitivity, and maintainability gates pass within the recorded platform/workload scope.')
decision={'state':state,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reasons':reasons,'gates':{'source_identity_and_separation':'PASS','three_full_source_release_builds':'PASS','debug_and_whole_library_sanitizer_builds':'PASS','relevant_upstream_and_conformance':'PASS','paired_correctness':'PASS','fault_destroy_and_same_instance_recovery':'PASS','leak_checks':'PASS','boundary_allocation_materiality':'PASS','timing_noninferiority':'FAIL_MATERIAL_SLOWDOWN' if slow else 'INCONCLUSIVE' if uncertain else 'PASS','injected_delay_sensitivity':'FAIL' if insensitive else 'PASS','maintainability':'CREDIBLE_SELF_REVIEW'},'counts':checks,'primary_material_slowdown_cells':slow,'primary_inconclusive_cells':uncertain,'sensitivity_failed_cells':insensitive,'paper_started':False,'reference_gate':'ACCEPTED_CLOSED; no further literature search','scope':['Native macOS arm64 Apple M5 Pro, Clang 21; no pooling of previous Debian archive evidence.','Three deterministic synthetic content families at 1080p and 4K; timing repetitions are technical repeats.','All 286 libaom archive object members compiled with ASan+UBSan or TSan flags. Whole-library instrumentation does not imply exhaustive path coverage.','Unoptimized broad encoder stress under sanitizers was interrupted; focused decoder conformance, faults and recovery passed. All 45 FPMT tests passed in a separate release configuration.','WebM CLI support disabled in the three primary builds; both official MKV vector payloads were extracted with the bundled parser and checked against official per-frame MD5 in 100 supplemental runs.','Upstream acceptance and external maintainability review are not claimed.']}
(root/'decision.json').write_text(json.dumps(decision,indent=2)+'\n')
(root/'results/final_upstream_summary.json').write_text(json.dumps(upstream,indent=2)+'\n')
lock=json.loads((root/'protocol/protocol.json').read_text())
top={'STOP':'冻结门禁触发停止，不能进入论文写作。','NARROW':'保留有限工程结果；门禁未全部通过，不能进入论文写作。','PASS_TO_PAPER_OUTLINE':'本次限定范围内的工程门禁通过；本任务没有开始论文或提纲写作。'}[state]
lines=[f'# CDEF full-source gate：{state}', '', top, '', '本报告仅汇总新的源码实验，不把交接包的 archive 原型结果合并为本次证据。三份 Priority-0 前作核查按用户指令保持关闭，未继续检索。', '', '## 源码与三变体', '', '- 已取得完整、可写的 Debian `aom 3.12.1-1` 源码。两个源码包文件 SHA-256 与 `.dsc` 一致。', '- 官方 `v3.12.1` 提交：`10aece4157eb79315da205f39e19bf6ab3ee30d0`；Git tree：`f401599b7be4c53cbcc2735969a4970c744dd372`。Debian orig 的 1,347 个对应文件全部与官方 Git blob 一致，无缺失或内容差异。', '- `baseline`、`type_fix`、`token` 各有独立源码树、构建目录、库和可执行文件。baseline manifest 复核一致；type_fix 仅改一处 sizeof；token 增量只涉及 3 个源文件，+115/-12 行。', '- 主配置统一为 Release，编码器/解码器/高位深均启用，`CONFIG_LIBYUV=0`、`CONFIG_WEBM_IO=0`。Debug、ASan+UBSan、TSan 均从完整源码重建；286 个 libaom archive 成员全部有对应插桩编译命令。', '- 平台：macOS 26.6.2，Apple M5 Pro，18 核，48 GiB，Apple Clang 21.0.0，CMake 4.4.2。完整身份、参数及散列见 `source_identity.json` 和 `results/instrumentation_audit.json`。', '', '## 正确性与安全性', '', '| 检查 | 结果 |', '|---|---|', '| 三变体配对可见像素 SHA-256 与帧数 | 540 次通过 |', '| token Debug / ASan+UBSan / TSan 配对矩阵 | 各 180 次通过 |', '| 无效和截断输入，三 release 变体及两种 sanitizer | 750 次一致 |', '| 三变体上游 CDEF/common/decoder API | 各 208 项通过 |', '| 三变体 release conformance / 两种 sanitizer conformance | 各 3,899 项通过 |', '| token tile、row-MT 相关用例 | 508 个唯一用例最终通过 |', '| token resize、superres、frame-size、error resilience | 386 项通过 |', '| frame-parallel 专用配置 | 45 项通过，含全部 42 个 Large 用例 |', '| 上游 shell decoder 测试 | 三变体均通过 |', '| 两个官方 MKV resize 码流补验 | 100 次逐帧 MD5 符合官方值 |', '| 源码故障及负对照 | ASan+UBSan、TSan 各 156 次通过，各有 156 次后续干净解码 |', '| 同一 codec 实例出错后重新解码关键帧 | 两种 sanitizer 各 99 次通过 |', '| 系统 leaks 正常/故障销毁检查 | 36 次无泄漏；故意丢失分配的探针检出 32,768 字节 |', '', '配对矩阵覆盖 8/10/12-bit、mono/4:2:0/4:2:2/4:4:4、奇数尺寸、部分末行、单行/边缘尺寸、tiles、线程 1/2/4/8/16、row-MT off/on、编码的 frame-parallel 标记。故障包括冻结的五阶段、完整复制前/部分复制后、各平面 line buffer 分配以及 owner metadata 分配。', '', 'macOS ASan 不支持 LeakSanitizer，已保存实际探测日志；泄漏检查采用系统 leaks。声明的 sanitizer 结果限于实际执行路径。未把中断的、未优化的广泛编码压力套件算作通过。上游自带的 3 个 DISABLED resize speed 用例保持禁用；当前 CPU 不支持的 SVE 系列由上游框架排除。', '', '## 冻结内存结果', '', '| 4K、4:2:0，三个内容家族均一致 | boundary requested bytes | 相对 type_fix |', '|---|---:|---:|', '| baseline | 8,355,840 | 分开记录 sizeof 效应 |', '| type_fix | 2,088,960 | 基准 |', '| token，实际 W=8 | 522,240 | 减少 75.00% |', '| token，实际 W=16 | 1,013,760 | 减少 51.47% |', '', '额外的 token 逻辑元数据在 R=34 时为 W=8 的 356 字节、W=16 的 420 字节（未含该元数据 allocator padding）。1080p、R=17、W=16 属于 R 接近 W 的情况，边界请求字节仅减少 5.88%；收益明确依赖目标工况。', '', 'usable bytes 使用 libaom 对齐头指向的实际 malloc block 调用 malloc_size；进程峰值 RSS 使用 macOS getrusage，单位为字节。CDEF 阶段时间及行同步等待在独立 audit 构建记录；行同步等待不包括其他 codec 锁。池无容量等待路径，pool wait count 的零值是结构性结果。主要确认性计时使用没有这些日志插桩的 release 构建。完整结果在 `memory/memory_results.csv`，原始逐帧日志保留。', '', '## 冻结计时与灵敏度', '', f'- 协议 SHA-256：`{hashlib.sha256((root/"protocol/protocol.json").read_bytes()).hexdigest()}`。确认前锁定可执行文件、输入、主比较、阈值和随机种子。', '- 主比较为 token/type_fix；3 个固定合成内容家族 × 1080p/4K × 线程 2/8/16，共 18 个单元。每单元 1 个预热 pair、12 个 AB/BA 平衡 pair。', '- 主指标为 aom_codec_decode 调用及 flush 的累计单调时钟时间；预加载输入和可见像素哈希不计入该指标。每个过程的 RSS、时间、帧数、哈希和主机负载均保留。', '- 不劣阈值固定为 1.02；对 12 个配对比值的中位数做固定种子的 50,000 次 percentile bootstrap。上界 ≤1.02 才通过；下界 >1.02 触发实质减速停止；其余为无法确证不劣。未删除离群值或追加重复。', f'- 延迟对照使用同一 harness 和同一时间区域，每输入包注入 {lock["delay_ns_per_packet"]/1e6:.0f} ms；剂量在确认前校准。6 个对照单元各 12 个 pair，检出阈值、剂量核算和身份检查均按冻结规则判定。该大剂量对照不单独证明 2% 效应的检测能力。', '', '| 主比较单元 | W | token/type_fix 中位数 | 95% CI | 冻结判定 |', '|---|---:|---:|---|---|']
for x in timing:
    if x['kind']=='primary':lines.append(f'| {x["workload"]} | {x["threads"]} | {x["median_ratio"]:.4f} | [{x["ci95"][0]:.4f}, {x["ci95"][1]:.4f}] | {x["status"]} |')
lines += ['',f'灵敏度通过：{sum(x["status"]=="PASS" for x in timing if x["kind"]=="sensitivity")}/6。最终状态：**{state}**。', '', '## 可维护性、失败记录与范围', '', '动态所有权直接放入现有同步结构，沿用原有任务锁、行条件变量、错误唤醒和销毁路径。没有外部状态表、ABI 偏移或符号替换。消费行在过滤结束后才释放 incoming-top/own-bottom；不释放由下游消费的 outgoing-top。独立有限调度模型检查了 3,932 个状态，并给出固定 row-modulo ring 的合法别名反例。详见 `maintainability/review.md`。这是工程自审，不代表上游维护者已接受。', '', '保留的早期失败包括：Debian 镜像缺失 revision tar 后改用官方 snapshot；测试数据临时 TLS 失败及重试；aomenc 对非 4:2:0 的显式 12-bit profile 在初始化前设置 control 导致输入准备失败，改用原有自动 profile 升级且验证实际解码位深/抽样；数据未就绪时 80 个上游用例失败，校验完成后全部补跑通过；tarball 的 shell 测试误用 git describe，使用仅影响版本探测的 no-git shim；不可用的 LSan，以及没有有效诊断输出的早期 leaks 启动方式。以上都未删除或计入最终通过数。', '', '现有证据覆盖本机和记录的码流/调度/故障范围；不声称所有架构、所有合法 AV1 输入或所有未来调度均经过穷尽运行。RSS 及软件分配不作为硬件面积、功率或能量证据。全库插桩和原型 archive 的证据层级保持分离。', '', '**没有开始论文写作，也没有生成论文提纲。**', '']
(root/'RESULTS.md').write_text('\n'.join(lines))
print(state, 'material slowdown cells',len(slow),'inconclusive cells',len(uncertain),'sensitivity failures',len(insensitive))
