#!/usr/bin/env python3
"""Prepare isolated libaom trees and optionally build; original measurements remain read-only."""
from pathlib import Path
import argparse,hashlib,shutil,subprocess,tarfile,urllib.request,sys,os,json,platform
ROOT=Path(__file__).resolve().parents[1]
SHA='40c929a41b2a59c24319a699c358351422829b3ae646de31b18cbabed0191962'
URL='https://deb.debian.org/debian/pool/main/a/aom/aom_3.12.1.orig.tar.gz'
def run(cmd,cwd=None):print(' '.join(map(str,cmd)),flush=True);subprocess.run(list(map(str,cmd)),cwd=cwd,check=True)
def prepare(work,archive):
 source=work/'src';assert not source.exists(),'Use a new work directory; refusing source overwrite'
 work.mkdir(parents=True,exist_ok=True)
 if archive is None:
  archive=work/'aom_3.12.1.orig.tar.gz';urllib.request.urlretrieve(URL,archive)
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==SHA,'source archive digest mismatch'
 unpack=work/'unpacked';unpack.mkdir()
 with tarfile.open(archive) as t:t.extractall(unpack,filter='data')
 dirs=list(unpack.iterdir());assert len(dirs)==1 and dirs[0].is_dir()
 source.mkdir();shutil.move(str(dirs[0]),str(source/'baseline'))
 for name in (ROOT/'third_party/debian_patches/series').read_text().splitlines():
  if name.strip() and not name.startswith('#'):run(['patch','-p1','--fuzz=0','-i',ROOT/'third_party/debian_patches'/name],source/'baseline')
 shutil.copytree(source/'baseline',source/'type_fix');run(['patch','-p1','--fuzz=0','-i',ROOT/'patches/v3.12.1/baseline_to_type_fix.patch'],source/'type_fix')
 shutil.copytree(source/'type_fix',source/'token');run(['patch','-p1','--fuzz=0','-i',ROOT/'patches/v3.12.1/type_fix_to_token.patch'],source/'token')
 run([sys.executable,ROOT/'tools/make_audit_sources.py',work])
 (work/'source_identity.json').write_text(json.dumps({'source_url':URL,'archive_sha256':SHA,'version':'v3.12.1','upstream_commit':'10aece4157eb79315da205f39e19bf6ab3ee30d0'},indent=2)+'\n')
def link(src,lib,out):
 cmd=[os.environ.get('CC','cc'),'-O2','-g','-Wno-deprecated-declarations','-I'+str(src),str(ROOT/'tools/ivf_gate_portable.c'),str(lib),'-lm','-lpthread','-o',str(out)]
 if platform.system()!='Darwin':cmd+=['-lcrypto']
 out.parent.mkdir(parents=True,exist_ok=True);run(cmd)
def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','build','configure','link']);p.add_argument('--work',type=Path,required=True);p.add_argument('--archive',type=Path);p.add_argument('--variants',nargs='+',default=['baseline','type_fix','token','baseline_audit','type_fix_audit','token_audit']);p.add_argument('--jobs',type=int,default=4);p.add_argument('--source',type=Path);p.add_argument('--library',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();w=a.work.resolve()
 if a.mode=='prepare':prepare(w,a.archive.resolve() if a.archive else None);return
 if a.mode=='link':link(a.source.resolve(),a.library.resolve(),a.output.resolve());return
 for v in a.variants:
  src=w/'src'/v;b=w/'builds'/(v+'_release')
  run(['cmake','-S',src,'-B',b,'-DCMAKE_POLICY_VERSION_MINIMUM=3.5','-DENABLE_DOCS=OFF','-DCONFIG_LIBYUV=0','-DCONFIG_WEBM_IO=0','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DCMAKE_BUILD_TYPE=Release'])
  if a.mode=='build':run(['cmake','--build',b,'-j',str(a.jobs)]);link(src,b/'libaom.a',b/'ivf_gate')
if __name__=='__main__':main()
