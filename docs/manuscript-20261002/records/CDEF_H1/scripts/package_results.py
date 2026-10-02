from common import *
import zipfile
# No sources, inputs, scientific outcomes, stdout or stderr are deleted to package.
# Exclude reproducible build intermediates and read-only external upstream fixture cache only.
selected=set()
for area in ['src','inputs','protocol','scripts','history','patches','results','logs']:
 for p in (ROOT/area).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and 'shell_work' not in p.parts:selected.add(p)
for p in ROOT.glob('*'):
 if p.is_file() and p.suffix in ['.md','.csv','.json'] and p.name not in ['MANIFEST.json','COMMANDS.json','PACKAGE_VERIFICATION.json']:selected.add(p)
for p in (ROOT/'upstream').rglob('*'):
 if p.is_file() and 'aom.git' not in p.parts:selected.add(p)
for b in (ROOT/'builds').iterdir():
 if not b.is_dir():continue
 for name in ['aomenc','aomdec','test_libaom','ivf_gate','ivf_recovery','ivf_recreate','libaom.a','CMakeCache.txt','compile_commands.json','aom.pc']:
  p=b/name
  if p.is_file():selected.add(p)
 for p in (b/'config').glob('*'):
  if p.is_file():selected.add(p)
# The packager's own outer wrapper is still running. Include its command, but not an invented successful result.
commands=[]
for p in sorted((ROOT/'logs').glob('*.command.json')):
 if p.name.startswith('099_package.'):continue
 r=json.loads(p.read_text());result=p.with_name(p.name.replace('.command.json','.result.json'));rec=json.loads(result.read_text()) if result.exists() else r|{'exit_code':None,'status':'PACKAGE_WRAPPER_STILL_RUNNING_AT_SNAPSHOT'}
 rec['stdout']=str(p.with_name(p.name.replace('.command.json','.stdout')).relative_to(ROOT));rec['stderr']=str(p.with_name(p.name.replace('.command.json','.stderr')).relative_to(ROOT));commands.append(rec)
save(ROOT/'COMMANDS.json',commands);selected.add(ROOT/'COMMANDS.json')
# Do not put files still being written into the payload. Packager record is delivered separately after completion.
for p in list(selected):
 if p.parent==ROOT/'logs' and p.name.startswith('099_package.'):selected.remove(p)
manifest=[]
for p in sorted(selected):manifest.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
save(ROOT/'MANIFEST.json',{'format':'sha256-size-v1','self_excluded':True,'files':manifest});selected.add(ROOT/'MANIFEST.json')
state=json.loads((ROOT/'decision.json').read_text())['final_state'];stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=ROOT.parent/f'cdef_h1_{stamp}_results.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
 for p in sorted(selected):z.write(p,'CDEF_H1/'+str(p.relative_to(ROOT)))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for r in manifest:
  data=z.read('CDEF_H1/'+r['path']);assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],r['path']
sha_path=out.with_suffix('.zip.sha256');digest=sha(out);sha_path.write_text(digest+'  '+out.name+'\n')
save(ROOT/'PACKAGE_VERIFICATION.json',{'zip':str(out),'bytes':out.stat().st_size,'sha256':digest,'CRC':'PASS','manifest_files_verified':len(manifest),'zip_members':len(selected),'state':state,'exclusions':['disposable build object files and dSYM caches','bare Git objects (official archive snapshots and blob ledger included)','read-only upstream fixture cache (all 572 URLs and verified hashes supplied)','packager wrapper logs, still running at snapshot; final wrapper result delivered beside ZIP']})
print(json.dumps(json.loads((ROOT/'PACKAGE_VERIFICATION.json').read_text()),indent=2))
