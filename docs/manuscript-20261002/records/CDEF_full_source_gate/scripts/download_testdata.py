from pathlib import Path
import re, hashlib, json, subprocess, concurrent.futures, time
root = Path(__file__).resolve().parents[1]
source = root / 'src/baseline/test'
names = set(re.findall(r'"([^"\n]+\.(?:yuv|y4m|ivf|mkv|md5|res(?:\.[234])?|txt))"', (source/'test_data_util.cmake').read_text()))
entries=[]
for line in (source/'test-data.sha1').read_text().splitlines():
    checksum, name = line.split(' *', 1)
    if name in names: entries.append((checksum, name))
def get(entry):
    sha1, name=entry; p=root/'testdata'/name
    url='https://storage.googleapis.com/aom-test-data/'+name
    if not p.exists() or hashlib.sha1(p.read_bytes()).hexdigest()!=sha1:
        result=subprocess.run(['curl','-fsSL','--retry','2','--connect-timeout','15','--max-time','180',url,'-o',str(p)],capture_output=True,text=True)
        if result.returncode: return dict(name=name,status='download_failed',error=result.stderr,url=url)
    data=p.read_bytes()
    return dict(name=name,status='PASS' if hashlib.sha1(data).hexdigest()==sha1 else 'HASH_MISMATCH',sha1=sha1,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),url=url)
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for result in pool.map(get,entries):
        results.append(result)
        if len(results)%25==0: print(len(results),'/',len(entries),flush=True)
        (root/'results/testdata_manifest.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({'files':len(results),'failures':[x for x in results if x['status']!='PASS'],'bytes':sum(x.get('bytes',0) for x in results)}),flush=True)
