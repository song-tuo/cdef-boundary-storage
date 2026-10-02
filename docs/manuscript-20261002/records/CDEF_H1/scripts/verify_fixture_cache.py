from common import *
DATA=Path('${WORKSPACE}/CDEF_full_source_gate/testdata');expected={}
for line in (ROOT/'src/hybrid/test/test-data.sha1').read_text().splitlines():
 bits=line.split()
 if len(bits)==2:
  if len(bits[0])==40:expected[bits[1].lstrip('*')]=bits[0]
  elif len(bits[1])==40:expected[bits[0].lstrip('*')]=bits[1]
rows=[]
for p in sorted(DATA.iterdir()):
 if not p.is_file():continue
 h=hashlib.sha1();s=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b);s.update(b)
 rows.append({'name':p.name,'source_path':str(p),'bytes':p.stat().st_size,'sha1':h.hexdigest(),'sha256':s.hexdigest(),'upstream_expected_sha1':expected.get(p.name),'status':'MATCH_OFFICIAL' if h.hexdigest()==expected.get(p.name) else 'MISMATCH_OFFICIAL' if p.name in expected else 'NO_OFFICIAL_SHA1_ENTRY','url':'https://storage.googleapis.com/aom-test-data/'+p.name})
save(ROOT/'inputs/upstream_fixture_manifest.json',rows)
print('Cached official fixtures',len(rows),'mismatches',sum(r['status']=='MISMATCH_OFFICIAL' for r in rows))
