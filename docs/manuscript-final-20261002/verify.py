"""Check file integrity and evidence locators; no experiment or analysis."""
from pathlib import Path
import argparse,csv,hashlib,json,zipfile
p=argparse.ArgumentParser();p.add_argument('--evidence-zip',type=Path);a=p.parse_args()
r=Path(__file__).parent
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
m=json.loads((r/'MANIFEST.json').read_text())
for x in m['files']:
 f=r/x['path'];assert f.stat().st_size==x['bytes'] and sha(f)==x['sha256'],x['path']
if a.evidence_zip:
 b=json.loads((r/'EVIDENCE_BASE.json').read_text())
 assert a.evidence_zip.stat().st_size==b['bytes'] and sha(a.evidence_zip)==b['sha256']
 with zipfile.ZipFile(a.evidence_zip) as z:
  assert z.testzip() is None
  for row in csv.DictReader((r/'EVIDENCE_MAP.csv').open()):
   if row['evidence_root']=='artifact-v3 evidence ZIP root':
    for name in row['evidence_files'].split('; '):assert name in z.namelist(),name
  assert json.loads(z.read('records/CDEF_H1/decision.json'))['final_state']=='KEEP_DUAL_TOKEN_HYBRID_NOT_SUFFICIENT'
print('PASS: capsule integrity'+(' and exact v3 evidence asset/locators' if a.evidence_zip else '')+'; no experiments or statistics run')
