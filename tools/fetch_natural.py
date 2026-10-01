# Portable work root. Fetches licensed UVG raw prefixes, not historical output records.
#!/usr/bin/env python3
"""Read selected raw prefixes through immutable cached HTTP ranges, not whole archives."""
from pathlib import Path
import io,os,json,subprocess,time,hashlib,threading,concurrent.futures,sys
import py7zr
from py7zr.io import Py7zIO,WriterFactory
ROOT=Path(sys.argv[1]).resolve()/'natural'
for d in ['media','sources','logs']:(ROOT/d).mkdir(parents=True,exist_ok=True)
CHUNK=16*1024*1024
SIZES={'Beauty':4154000064,'Jockey':3453463918,'HoneyBee':3766406267}
RAW_BYTES=3840*2160*3//2*60

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
class PrefixComplete(Exception):pass
class RangeFile(io.RawIOBase):
 def __init__(self,name):
  self.name=name;self.pos=0;self.length=SIZES[name];self.cache=ROOT/'media'/f'{name}_ranges';self.cache.mkdir(exist_ok=True)
  self.url=f'https://tie-ultravideo.rd.tuni.fi/video/{name}_3840x2160_120fps_420_8bit_YUV_RAW.7z';self.records=[]
 def readable(self):return True
 def seekable(self):return True
 def tell(self):return self.pos
 def seek(self,offset,whence=0):
  self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.length+offset
  if self.pos<0:raise ValueError('negative seek')
  return self.pos
 def get_chunk(self,index):
  start=index*CHUNK;end=min(self.length,start+CHUNK)-1;p=self.cache/f'{start:012d}-{end:012d}.bin'
  if not p.exists():
   for attempt in range(3):
    partial=Path(str(p)+'.partial');header=Path(str(p)+f'.headers.{attempt}');log=Path(str(p)+f'.curl.{attempt}.log')
    cmd=['curl','--fail','--location','--silent','--show-error','--connect-timeout','30','--max-time','300','-r',f'{start}-{end}','-D',str(header),'-o',str(partial),self.url]
    t=time.time()
    with log.open('w') as f:ret=subprocess.run(cmd,stdout=f,stderr=f).returncode
    record={'start':start,'end':end,'attempt':attempt,'returncode':ret,'seconds':time.time()-t}
    self.records.append(record)
    with (self.cache/'requests.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
    if ret==0 and partial.stat().st_size==end-start+1 and f'bytes {start}-{end}/{self.length}' in header.read_text():
     partial.rename(p);print(self.name,'range',start,end,'seconds',round(record['seconds'],2),flush=True);break
    if attempt==2:raise IOError((self.name,'range failed',start,end))
    time.sleep(1)
  if p.stat().st_size!=end-start+1:raise IOError('cached length mismatch')
  return p
 def read(self,size=-1):
  if size is None or size<0:size=self.length-self.pos
  size=min(size,self.length-self.pos)
  out=bytearray()
  while size>0:
   index=self.pos//CHUNK;within=self.pos%CHUNK;p=self.get_chunk(index)
   take=min(size,p.stat().st_size-within)
   with p.open('rb') as f:f.seek(within);out.extend(f.read(take))
   self.pos+=take;size-=take
  return bytes(out)
 def readinto(self,b):
  s=self.read(len(b));b[:len(s)]=s;return len(s)
class PrefixWriter(Py7zIO):
 def __init__(self,path):self.f=path.open('xb');self.n=0
 def write(self,b):
  remaining=RAW_BYTES-self.n;self.f.write(b[:remaining]);self.n+=min(len(b),remaining)
  if self.n==RAW_BYTES:self.f.flush();self.f.close();raise PrefixComplete()
  return len(b)
 def read(self,size=None):raise io.UnsupportedOperation()
 def seek(self,offset,whence=0):raise io.UnsupportedOperation()
 def flush(self):
  if not self.f.closed:self.f.flush()
 def size(self):return self.n
class Factory(WriterFactory):
 def __init__(self,p):self.p=p;self.calls=[]
 def create(self,filename):
  if self.calls:raise RuntimeError('multiple archive outputs unexpectedly')
  self.calls.append(filename);self.writer=PrefixWriter(self.p);return self.writer

def fetch(name):
 out=ROOT/'media'/f'{name}_3840x2160_first60.yuv';result=ROOT/'sources'/f'{name}.json'
 if result.exists():return json.loads(result.read_text())
 assert not out.exists(),'Partial output exists; inspect before retry'
 r=RangeFile(name)
 try:
  with py7zr.SevenZipFile(r,'r') as z:
   infos=[{'filename':i.filename,'uncompressed':i.uncompressed,'compressed':i.compressed,'is_directory':i.is_directory} for i in z.list()]
   candidates=[i for i in infos if i['filename'].lower().endswith('.yuv') and not i['is_directory']]
   assert len(candidates)==1,infos
   assert candidates[0]['uncompressed']==3840*2160*3//2*600,candidates
   factory=Factory(out)
   try:z.extract(targets=[candidates[0]['filename']],factory=factory)
   except PrefixComplete:pass
   assert out.stat().st_size==RAW_BYTES
 except Exception:
  (ROOT/'logs'/f'{name}_fetch_failure.json').write_text(json.dumps({'name':name,'output_exists':out.exists(),'size':out.stat().st_size if out.exists() else 0},indent=2));raise
 d={'name':name,'url':r.url,'archive_bytes':r.length,'archive_members':infos,'selected_member':candidates[0]['filename'],'prefix_frames':60,'width':3840,'height':2160,'pixel_format':'yuv420p8','raw_bytes':RAW_BYTES,'raw_sha256':sha(out),'raw_path':str(out),'full_archive_crc_verified':False,'integrity_scope':'7z header parsed and prefix decompressed; full archive stream/member CRC requires all 600 frames and was not tested','compressed_ranges':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(r.cache.glob('*.bin'))],'retrieved_at_unix':time.time()}
 result.write_text(json.dumps(d,indent=2)+'\n');print('COMPLETE',name,d['raw_sha256'],flush=True);return d
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
  results=list(ex.map(fetch,['Beauty','Jockey','HoneyBee']))
 (ROOT/'sources/source_manifest.json').write_text(json.dumps(results,indent=2)+'\n')
