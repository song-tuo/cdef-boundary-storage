from checks import *
import concurrent.futures,xml.etree.ElementTree as ET
DATA=Path('${WORKSPACE}/CDEF_full_source_gate/testdata')
groups={'core':'*CDEF*:*CommonInt*:*AomMemTest*:*BlockdTest*:*Av1Config*:*DecodeAPI*:-*Speed*','conformance':'*TestVectorTest*:*InvalidFileTest*:*ExternalFrameBuffer*:*DecodeScalabilityTest*','row_tiles':'*DecodeMultiThreaded*:*ExtTileTest*:*TileIndependence*:*TileGroup*:*UniformTileConfig*','resize_error':'*Resize*:*Superres*:*FrameSize*:*ErrorResilience*'}
# Sharding changes only dispatch; every selected upstream case remains selected.
jobs=[(p,g,shard,4) for p,g in [('release','core'),('debug','core'),('asan','core'),('tsan','core'),('release','conformance'),('asan','conformance'),('tsan','conformance'),('release','row_tiles'),('release','resize_error')] for shard in range(4)]
def job(t):
 p,g,shard,n=t;tag=f'upstream_{p}_{g}_s{shard}';xml=ROOT/'results'/(tag+'.xml');cmd=[ROOT/'builds'/f'hybrid_{p}'/'test_libaom','--gtest_filter='+groups[g],'--gtest_output=xml:'+str(xml)]
 r=run(tag,cmd,env=SANENV|{'LIBAOM_TEST_DATA_PATH':str(DATA),'GTEST_TOTAL_SHARDS':str(n),'GTEST_SHARD_INDEX':str(shard)},timeout=7200);count=fail=skip=disabled=0
 if xml.exists():
  tree=ET.parse(xml).getroot();tests=tree.findall('.//testcase');count=len(tests);fail=sum(len(t.findall('failure'))>0 for t in tests);skip=sum(t.get('status')=='notrun' or bool(t.findall('skipped')) for t in tests);disabled=int(tree.get('disabled',0))
 return {'category':'upstream','profile':p,'group':g,'shard':shard,'exit_code':r['exit_code'],'tests':count,'failed':fail,'skipped':skip,'disabled':disabled,'status':'PASS' if r['exit_code']==0 and count>0 and fail==0 and skip==0 else 'FAIL' if r['exit_code'] or fail else 'INCOMPLETE','command_log':tag}
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for row in ex.map(job,jobs):
  rows.append(row);save(ROOT/'results/upstream_progress.json',rows)
writecsv('results/upstream_safety.csv',rows)
