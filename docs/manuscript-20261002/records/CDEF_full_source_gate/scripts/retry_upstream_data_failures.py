from pathlib import Path
import xml.etree.ElementTree as ET
import subprocess,os,json,concurrent.futures
root=Path(__file__).resolve().parents[1]
xml=root/'results/token_release_upstream_row_tiles.xml'
cases=[x.attrib['classname']+'.'+x.attrib['name'] for x in ET.parse(xml).iter('testcase') if x.find('failure') is not None]
(root/'results/row_tiles_retry_plan.json').write_text(json.dumps(dict(reason='First run began before all test-data retries completed; retain first failures, retry every failed case once after hash verification.',cases=cases),indent=2)+'\n')
assert cases
def shard(i):
    stem=f'token_release_row_tiles_retry_shard{i}';cmd=[str(root/'builds/token_release/test_libaom'),'--gtest_filter='+':'.join(cases),'--gtest_output=xml:'+str(root/'results'/(stem+'.xml'))]
    env=dict(os.environ,LIBAOM_TEST_DATA_PATH=str(root/'testdata'),GTEST_TOTAL_SHARDS='4',GTEST_SHARD_INDEX=str(i))
    with (root/'logs'/(stem+'.log')).open('w') as f:
        try:code=subprocess.run(cmd,stdout=f,stderr=f,timeout=1800,env=env).returncode
        except subprocess.TimeoutExpired:code='TIMEOUT_1800s'
    return dict(shard=i,exit=code,command=cmd)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:res=list(pool.map(shard,range(4)))
(root/'results/row_tiles_retry_status.json').write_text(json.dumps(res,indent=2)+'\n');print([(r['shard'],r['exit']) for r in res],flush=True)
