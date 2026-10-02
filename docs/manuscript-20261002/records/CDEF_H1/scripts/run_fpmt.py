from checks import *
import concurrent.futures,xml.etree.ElementTree as ET
b=ROOT/'builds/hybrid_fpmt';s=ROOT/'src/hybrid'
cmd=['cmake','-S',s,'-B',b,'-DCMAKE_POLICY_VERSION_MINIMUM=3.5','-DENABLE_DOCS=OFF','-DCONFIG_LIBYUV=0','-DCONFIG_WEBM_IO=0','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_BUILD_TYPE=Release','-DCONFIG_FPMT_TEST=1']
for tag,cmd in [('fpmt_configure',cmd),('fpmt_build',['cmake','--build',b,'-j','6'])]:
 r=run(tag,cmd);assert not r['exit_code']
save(ROOT/'protocol/FPMT_BUILD_SEAL.json',{'source_seal':'IMPLEMENTATION_SEAL.json','files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [b/'test_libaom',b/'libaom.a',b/'compile_commands.json',b/'CMakeCache.txt']]})
def job(shard):
 tag=f'fpmt_s{shard}';xml=ROOT/'results'/(tag+'.xml');r=run(tag,[b/'test_libaom','--gtest_filter=*FrameParallelThreadEncode*','--gtest_output=xml:'+str(xml)],env={'LIBAOM_TEST_DATA_PATH':'${WORKSPACE}/CDEF_full_source_gate/testdata','GTEST_TOTAL_SHARDS':'4','GTEST_SHARD_INDEX':str(shard)},timeout=7200)
 tests=ET.parse(xml).getroot().findall('.//testcase') if xml.exists() else [];failed=sum(bool(t.findall('failure')) for t in tests);skipped=sum(bool(t.findall('skipped')) or t.get('status')=='notrun' for t in tests)
 return {'category':'encoder_frame_parallel','profile':'CONFIG_FPMT_TEST=1','shard':shard,'tests':len(tests),'failed':failed,'skipped':skipped,'exit_code':r['exit_code'],'status':'PASS' if not r['exit_code'] and tests and not(failed or skipped) else 'FAIL','command_log':tag}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(job,range(4)))
writecsv('results/fpmt_safety.csv',rows)
