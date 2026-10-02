from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'CDEF_潤色修訂版_20261002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (ROOT/'results/timing_summary.json').exists()
assert json.loads((ROOT/'results/GATES_PASS.json').read_text())['passed']==486
files={}
for folder in ['scripts','patches','results','logs','protocol']:
 for p in sorted((ROOT/folder).rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
  if p.name.startswith('processes_'):continue # Full desktop process inventory stays local.
  files[str(p.relative_to(ROOT))]=p
files['README.md']=ROOT/'README.md'
for n in ['LICENSE','PATENTS','AUTHORS']:files['libaom_'+n]=ROOT/'src/token'/n
manifest={n:{'sha256':sha(p),'bytes':p.stat().st_size} for n,p in files.items()}
mp=ROOT/'MANIFEST.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');files['MANIFEST.json']=mp
out=BASE/'04_ring對照_補充資料.zip';prefix='CDEF_ring_comparison_20261002'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for n,p in files.items():z.write(p,f'{prefix}/{n}')
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for n,p in files.items():assert z.read(f'{prefix}/{n}')==p.read_bytes()
print(json.dumps(dict(zip=str(out),files=len(files),bytes=out.stat().st_size,sha256=sha(out)),indent=2))
