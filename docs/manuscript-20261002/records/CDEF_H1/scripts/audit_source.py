from common import *
repo=ROOT/'upstream/aom.git';paths=['av1/common/alloccommon.c','av1/common/thread_common.c','av1/common/thread_common.h','av1/common/cdef.c','av1/common/cdef.h','av1/decoder/decodeframe.c','av1/decoder/decoder.c','av1/encoder/ethread.c','av1/encoder/encoder.c']
expected={'v3.12.1':'10aece4157eb79315da205f39e19bf6ab3ee30d0','v3.15.1':'44d0a57786f432d933ff64b653347c66f4d0fa1d'};records=[]
for tag in ['v3.12.1','v3.15.1','main']:
 name=tag.replace('.','_');r=run('003_'+name+'_identity',['git','-C',repo,'rev-parse',tag+'^{commit}']);assert r['exit_code']==0;commit=(ROOT/'logs'/('003_'+name+'_identity.stdout')).read_text().strip()
 if tag in expected:assert commit==expected[tag]
 run('004_'+name+'_tree',['git','-C',repo,'ls-tree','-r',commit]);listing={line.split('\t')[1]:line.split()[2] for line in (ROOT/'logs'/('004_'+name+'_tree.stdout')).read_text().splitlines()}
 run('005_'+name+'_archive',['git','-C',repo,'archive','--format=tar','-o',ROOT/'upstream'/(tag+'.tar'),commit])
 for path in paths:
  log='006_'+name+'_'+path.replace('/','_').replace('.','_');r=run(log,['git','-C',repo,'show',commit+':'+path]);assert r['exit_code']==0
  data=(ROOT/'logs'/(log+'.stdout')).read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert blob==listing[path]
  p=ROOT/'upstream'/tag/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  records.append({'version':tag,'commit':commit,'path':path,'git_blob':blob,'sha256':sha(p),'bytes':len(data)})
save(ROOT/'results/source_identity.json',records)
print(json.dumps(records,indent=2))
