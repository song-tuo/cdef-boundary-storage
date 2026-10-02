from checks import *
import concurrent.futures,xml.etree.ElementTree as ET
# Same frozen production+diagnostic source; the non-Large upstream FPMT cases are fixed before these builds/runs.
save(ROOT/'protocol/FPMT_SANITIZER_EXECUTION.json',{'profiles':['asan','tsan'],'source':'hybrid_audit (same implementation seal)','filter':'*FrameParallelThreadEncode*:-*Large*','reason':'independent sanitizer check of the changed per-worker state on encoder frame-parallel path; supplement to all 45 clean Release tests','frozen_before_build_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
def job(p):
 b=ROOT/'builds'/f'hybrid_audit_fpmt_{p}';s=ROOT/'src/hybrid_audit';san={'asan':'address,undefined','tsan':'thread'}[p]
 cmd=['cmake','-S',s,'-B',b,'-DCMAKE_POLICY_VERSION_MINIMUM=3.5','-DENABLE_DOCS=OFF','-DCONFIG_LIBYUV=0','-DCONFIG_WEBM_IO=0','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_BUILD_TYPE=Debug','-DCONFIG_FPMT_TEST=1','-DSANITIZE='+san]
 for tag,cmd in [(f'fpmt_{p}_configure',cmd),(f'fpmt_{p}_build',['cmake','--build',b,'-j','6'])]:
  r=run(tag,cmd)
  if r['exit_code']:return {'category':'encoder_frame_parallel_sanitizer','profile':p,'exit_code':r['exit_code'],'status':'BUILD_FAILED','command_log':tag}
 save(ROOT/'protocol'/f'FPMT_{p}_BUILD_SEAL.json',{'files':[{'path':str(x.relative_to(ROOT)),'sha256':sha(x)} for x in [b/'test_libaom',b/'libaom.a',b/'compile_commands.json',b/'CMakeCache.txt']]})
 tag=f'fpmt_{p}_small';xml=ROOT/'results'/(tag+'.xml');r=run(tag,[b/'test_libaom','--gtest_filter=*FrameParallelThreadEncode*:-*Large*','--gtest_output=xml:'+str(xml)],env=SANENV|{'LIBAOM_TEST_DATA_PATH':'${WORKSPACE}/CDEF_full_source_gate/testdata'},timeout=3600)
 tests=ET.parse(xml).getroot().findall('.//testcase') if xml.exists() else [];failed=sum(bool(t.findall('failure')) for t in tests);skipped=sum(bool(t.findall('skipped')) or t.get('status')=='notrun' for t in tests);text=(ROOT/'logs'/(tag+'.stderr')).read_text(errors='replace');sanerror=any(k in text for k in ['ERROR: AddressSanitizer','WARNING: ThreadSanitizer','runtime error:','"h1":"violation"'])
 return {'category':'encoder_frame_parallel_sanitizer','profile':p,'tests':len(tests),'failed':failed,'skipped':skipped,'exit_code':r['exit_code'],'sanitizer':sanerror,'status':'PASS' if not r['exit_code'] and len(tests)==3 and not(failed or skipped or sanerror) else 'FAIL','command_log':tag}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:rows=list(ex.map(job,['asan','tsan']))
writecsv('results/fpmt_sanitizer_safety.csv',rows)
