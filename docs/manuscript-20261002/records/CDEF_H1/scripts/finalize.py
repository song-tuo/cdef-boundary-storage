from checks import *
import xml.etree.ElementTree as ET,shutil
loadcsv=lambda n:list(csv.DictReader((ROOT/n).open()))
sem=loadcsv('semantic_matrix.csv');fault=loadcsv('fault_recovery.csv');profiles=loadcsv('results/safety_profiles.csv');up=loadcsv('results/upstream_safety.csv');fp=loadcsv('results/fpmt_safety.csv');fpsan=loadcsv('results/fpmt_sanitizer_safety.csv');mkv=loadcsv('results/mkv_safety.csv');leaks=loadcsv('results/leak_native_safety.csv');shell=loadcsv('results/shell_safety.csv');activity=loadcsv('results/timing_activity.csv');timing=loadcsv('timing_summary.csv');real=loadcsv('real_content.csv');account=loadcsv('allocation_accounting.csv')
# Keep original observational tables; enrich the required top-level tables with derived metadata.
for raw,detail in [('allocation_accounting.csv','results/allocation_details.csv'),('real_content.csv','results/real_content_activity_details.csv')]:
 shutil.copyfile(ROOT/raw,ROOT/'results'/('raw_'+raw));shutil.copyfile(ROOT/detail,ROOT/raw)
for r in up:
 r['default_disabled_count']=r['disabled'];r['executed_test_count']=int(r['tests'])-int(r['disabled']);r['supported_selected_status']='PASS' if int(r['exit_code'])==0 and int(r['failed'])==0 and int(r['skipped'])==int(r['disabled']) else 'INCOMPLETE';r['accounting_note']='Original inventory status retained; default-disabled cases are not counted as executed PASS'
safety=profiles+mkv+leaks+shell+fp+fpsan+up
for r in loadcsv('results/leak_safety.csv'):safety.append(r|{'category':'sandbox_leak_attempt','required_coverage':'supplied by independent native leak check; this attempt is not PASS'})
for p in sorted((ROOT/'results').glob('upstream_*.xml'))+sorted((ROOT/'results').glob('fpmt_s*.xml')):
 for t in ET.parse(p).getroot().findall('.//testcase'):
  failed=t.findall('failure');skipped=t.findall('skipped');disabled='DISABLED_' in (t.get('classname','')+'.'+t.get('name',''))
  status='FAIL' if failed else 'DISABLED_NOT_EXECUTED' if disabled and t.get('status')=='notrun' else 'SKIPPED' if skipped or t.get('status')=='notrun' else 'PASS'
  safety.append({'category':'upstream_individual','profile':p.stem,'test_class':t.get('classname'),'test_name':t.get('name'),'seconds':t.get('time'),'status':status,'details':'\n'.join(x.get('message','') for x in failed+skipped),'xml':str(p.relative_to(ROOT))})
safety.append({'category':'architecture','profile':'SVE','status':'UNSUPPORTED','required_coverage':'SVE/SVE2 objects are compiled, but upstream runtime CPU detection appends their negative gtest filters on this host; no SVE PASS claimed'})
fields=list(dict.fromkeys(k for r in safety for k in r));writecsv('safety_matrix.csv',safety,fields)
seal=json.loads((ROOT/'protocol/IMPLEMENTATION_SEAL.json').read_text());changed=[r['path'] for r in seal['files'] if sha(ROOT/r['path'])!=r['sha256']];save(ROOT/'results/final_seal_recheck.json',{'files':len(seal['files']),'changed':changed})
timing_semantic_mismatch=any(r.get('block_hash_match')=='False' for r in loadcsv('timing_blocks.csv'))
sem_ok=all(r['status']=='PASS' for r in sem+real+mkv+activity) and not timing_semantic_mismatch
up_supported=[r for r in safety if r.get('category')=='upstream_individual' and r['status']!='DISABLED_NOT_EXECUTED']
safety_ok=all(r['status']=='PASS' for r in profiles+fault+fp+fpsan+leaks+shell+up_supported) and all(int(r['exit_code'])==0 and int(r['failed'])==0 for r in up)
capacity_ok=all(r['status']=='PASS' for r in account);timing_ok=all(r['status']=='PASS_LOCAL_NONINFERIORITY' for r in timing)
state='STOP_CDEF_HYBRID_SEMANTICS' if not sem_ok else 'PROCEED_CDEF_HYBRID_AS_MINIMAL_REALIZATION' if safety_ok and capacity_ok and timing_ok and not changed else 'KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT'
reasons=[]
if not sem_ok:reasons.append('semantic_or_official_frame_or_copy_mismatch')
if not safety_ok:reasons.append('independent_hybrid_safety_required_coverage_not_all_pass')
if not capacity_ok:reasons.append('capacity_accounting_not_all_pass')
if not timing_ok:reasons.append('prospective_local_block_noninferiority_not_established_in_all_18_cells')
if changed:reasons.append('frozen_input_source_or_binary_changed')
if not reasons:reasons=['all_frozen_gates_pass']
counts={'semantic_unique_configurations':432,'semantic_records':len(sem),'hybrid_debug_asan_tsan_records':len(profiles),'fault_and_recovery_records':len(fault),'allocation_records':len(account),'real_content_records':len(real),'official_mkv_records':len(mkv),'native_leak_records':len(leaks),'timing_cells':len(timing),'timing_blocks':216,'timed_processes':648,'upstream_selected_tests_by_profile_group':{},'fpmt_sanitizer_tests':sum(int(r.get('tests',0)) for r in fpsan),'fpmt_tests':sum(int(r['tests']) for r in fp)}
for r in up:
 k=r['profile']+'/'+r['group'];counts['upstream_selected_tests_by_profile_group'][k]=counts['upstream_selected_tests_by_profile_group'].get(k,0)+int(r['tests'])
save(ROOT/'decision.json',{'candidate':'CDEF','stage':'H1 SIMPLE-BOTTOM / HYBRID CONFIRMATORY GATE','final_state':state,'reasons':reasons,'source_drift_resolved':False,'semantic_gate':sem_ok,'safety_gate':safety_ok,'capacity_gate':capacity_ok,'timing_gate':timing_ok,'read_only_prior_results':True,'U_permanently_stopped':True,'AL_not_resumed':True,'serial_W1':'unchanged compatibility only, user confirmed','counts':counts,'timing_scope':'frozen host/workload only; no universal 2% or speedup claim','paper_disposition':{'main_implementation':'hybrid','dual_token':'design exploration/control','contributions':['source-derived lifetime contract','tight finite-frame live-boundary bound','minimal realization of that bound'],'old_paper_modified':False} if state.startswith('PROCEED') else {'old_paper_modified':False,'no_hybrid_main_implementation_promotion':True}})
lines=['# CDEF-H1 决策报告','',f'最终状态：**{state}**','', '本轮只执行 CDEF-H1；旧 CDEF、U、AL 结果未覆盖，U 和 AL 不恢复。W=1 按用户确认保留串行路径，只验证兼容性。','', '## 门禁与证据','',f'- Source drift：v3.12.1、v3.15.1 与固定 main `ae410fe8b7bd45f3cf61dc8f112dc783e2a08089` 均保留 frame-row-indexed 边界存储，没有等价解决；27 个相关 Git blob 已校验。',f'- 精确语义：432 个配置 × 三实现 × clean/audit，共 {len(sem)} 条记录；失败 {sum(r["status"]!="PASS" for r in sem)}。覆盖高位深、420/444、row-MT 开关、W/R 边界、CDEF 开关和同实例尺寸增减。',f'- hybrid 独立 Debug/ASan+UBSan/TSan：{len(profiles)} 条，失败 {sum(r["status"]!="PASS" for r in profiles)}。五个 Debug/sanitizer 库各 286 个成员核对编译参数。',f'- 注入与恢复：{len(fault)} 条，失败 {sum(r["status"]!="PASS" for r in fault)}；完整错误与预期非零退出码保留。',f'- 官方 MKV resize：{len(mkv)} 次逐帧 MD5 比对；native leaks：{len(leaks)} 次，失败 {sum(r["status"]!="PASS" for r in leaks)}。沙箱内 task-port 失败另列，不计 PASS。',f'- Encoder frame-parallel：{counts["fpmt_tests"]} 项独立 Release 测试，并补验 ASan+UBSan / TSan 各三个固定小用例；状态见 safety_matrix.csv。','', '| 上游选择组 | 测试记录 |','|---|---:|']
for k,n in counts['upstream_selected_tests_by_profile_group'].items():lines.append(f'| {k} | {n} |')
lines+=['','三个 resize 分片的原始汇总标为 INCOMPLETE，是因为每个 XML 列出一个上游默认禁用的 DISABLED_Speed 用例。逐项表将其记为 DISABLED_NOT_EXECUTED，不计入执行 PASS；受支持且实际选择执行的 correctness 用例另行验收。所有 skipped/unsupported、禁用测试和失败日志均单独保留；不把架构不支持的 SVE 路径算作通过。上游 WebM CLI 在该构建中关闭，两个原有 MKV resize 内容由原始 AV1 payload 加官方逐帧 MD5 独立补验。','', '## 容量与实现复杂度','', '27 条分辨率/worker/实现记录测量实际 requested 与 backing-block usable bytes。Hybrid 的 MT strip 数精确等于 min(2R−2,2W+1)，bottom owner 数组、free-slot scan、capacity wait 均不存在。每行地址索引仍保留，并单独计入；原有同步元数据仍随 R 变化，因此不把整个解码器内存说成仅随 W 变化。','', '4K、W=8：type_fix 像素边界请求 2,088,960 B；dual_token 与 hybrid 均为 522,240 B，减少 75%。Hybrid owner 请求从 68 B 降到 36 B，但 worker 结构从 3,904 B 增到 3,968 B；删除 owner 状态不意味着总元数据更小。所有 allocator padding 单列。这些不是 RSS、SRAM、area、power 或 energy。','', '## 新 block 计时','', '每个 cell 为 12 个完整三实现 block；六种顺序各两次。置信区间重采样单位只有 block，50,000 次，所有 648 次测量保留，没有邻接 pair 独立样本假设、旧 token CI、离群值删除或结果后追加。仅支持冻结本机 workload 下的结论。主要比较 hybrid/type_fix；次要 dual_token/hybrid 见 timing_summary.csv。','', '| workload | resolution | W | hybrid/type_fix 中位数 | 95% CI | 判定 |','|---|---|---:|---:|---|---|']
for r in timing:lines.append(f'| {r["family"]} | {r["width"]}×{r["height"]} | {r["W_requested"]} | {float(r["hybrid_type_fix_median"]):.4f} | [{float(r["ci95_low"]):.4f}, {float(r["ci95_high"]):.4f}] | {r["status"]} |')
lines+=['','1.02 是事前冻结的本机非劣 margin；区间越过它不能记为已证实非劣。不作 universal ≤2% overhead 或 speedup 声明。','', '## 固定真实内容','', '三个官方源的 ID、SHA-256 和三档编码设置均在解码和计时前冻结。所有 9 个码流 × W=2/8/16 × 三实现共 81 条均保留。真实内容无需依据 timing 替换。下表为 W=8 hybrid 的实际非零强度 luma 8×8 块占可见块比例；0 强度方向计算单独计数，避免把方向计算等同像素滤波。低/中/高仅指这些固定内容内观测到的活动范围，不是总体内容分类。','', '| 内容 | q0 | q24 | q56 |','|---|---:|---:|---:|']
detail=loadcsv('real_content.csv')
for prefix in ['real_park_joy_90p_8_420','real_crowd_run_360p_10_150f','real_wikipedia_420_360p_60f']:
 values=[next(r for r in detail if r['input']==prefix+f'_q{q}' and r['variant']=='hybrid' and r['W_requested']=='8') for q in [0,24,56]];lines.append('| '+prefix+' | '+' | '.join(f'{100*float(r["nonzero_luma_fraction"]):.2f}%' for r in values)+' |')
lines+=['','## 保留与限制','', '主协议、实现 seal、输入 hash、源码、patch、全部实验 stdout/stderr/退出码均保留。source preparation 和诊断头文件的编译错误发生于第一轮科学解码前，未改科研设置。详细归因见 PATCH_LEDGER.md。','', '本轮决定理由：'+', '.join(reasons)+'.','', '只有 PROCEED 才把 hybrid 定为新论文主实现，并将 dual-token 降为探索/对照；本轮始终不覆盖旧论文文件。未通过时不作该提升，也不修改实现、门槛或输入来补救本轮。']
(ROOT/'RESULTS.md').write_text('\n'.join(lines)+'\n')
print(state)
