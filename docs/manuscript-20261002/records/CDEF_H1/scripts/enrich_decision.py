from checks import *
rows=list(csv.DictReader((ROOT/'timing_summary.csv').open()));counts=Counter(r['status'] for r in rows);counts['EXPLICIT_LOCAL_REGRESSION']+=0
p=ROOT/'decision.json';d=json.loads(p.read_text());d['timing_status_counts']=dict(counts);d['explicit_local_timing_regression_detected']=bool(counts['EXPLICIT_LOCAL_REGRESSION']);d['interpretation']='Hybrid attains the finite-frame strip bound and passes the executed semantic/safety checks. Promotion is withheld because the prospective all-cell local noninferiority gate is not established; no cell has an explicit local regression.';save(p,d)
p=ROOT/'RESULTS.md';s=p.read_text();anchor='最终状态：**KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT**\n';assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\nKEEP 由事前冻结的计时确认门触发：6/18 个 cell 通过 1.02 非劣 margin，12 个区间仍不确定，明确性能退化为 0 个。Hybrid 已达到有限帧 strip 容量界，并通过本轮实际执行的语义与安全检查；本轮不据此升级论文主实现。\n');p.write_text(s)
print(dict(counts))
