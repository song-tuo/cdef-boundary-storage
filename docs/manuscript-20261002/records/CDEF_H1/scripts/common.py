from pathlib import Path
import subprocess,json,datetime,hashlib,os,time
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def run(name,cmd,cwd=None,env=None,timeout=None):
 stem=ROOT/'logs'/name;stem.parent.mkdir(parents=True,exist_ok=True)
 if stem.with_suffix('.command.json').exists():raise RuntimeError('refusing overwrite '+str(stem))
 rec={'name':name,'command':list(map(str,cmd)),'cwd':str(cwd or ROOT),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment_delta':env or {}}
 save(stem.with_suffix('.command.json'),rec);t=time.monotonic();timedout=False
 with stem.with_suffix('.stdout').open('wb') as o,stem.with_suffix('.stderr').open('wb') as e:
  try:p=subprocess.run(rec['command'],cwd=rec['cwd'],env=os.environ|(env or {}),stdout=o,stderr=e,timeout=timeout);code=p.returncode
  except subprocess.TimeoutExpired:code=124;timedout=True
 rec.update(exit_code=code,timed_out=timedout,wall_seconds=time.monotonic()-t);save(stem.with_suffix('.result.json'),rec)
 print(name,'exit',code,flush=True);return rec
if __name__=='__main__':
 import sys
 raise SystemExit(run(sys.argv[1],sys.argv[2:])['exit_code'])
