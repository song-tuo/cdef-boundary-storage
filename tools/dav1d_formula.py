#!/usr/bin/env python3
"""Portable algebra recheck; optional verification of separately obtained pinned source."""
from pathlib import Path
import importlib.util,argparse,json,itertools,hashlib,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evidence/dav1d'
spec=importlib.util.spec_from_file_location('original_dav1d_algebra',E/'verify_formula.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path);a=p.parse_args();source_checks=0
if a.source_dir:
 record=json.loads((E/'verification.json').read_text())
 for name,item in record['source_hashes'].items():
  part=name.removeprefix('code/dav1d_');rel=('src/'+part[4:]) if part.startswith('src_') else part
  assert hashlib.sha256((a.source_dir/rel).read_bytes()).hexdigest()==item['sha256'],rel;source_checks+=1
hcount=0
for h,b in itertools.product(range(1,131073),(0,1)):
 assert m.source_sbh(h,b)==m.closed_sbh(h,b);hcount+=1
acount=0
for y,uv,s,n,resize in itertools.product((-8192,-3840,-1920,-1,1,1920,3840,8192),(-4096,-1920,-960,0,960,1920,4096),(1,2,9,17,34,65),(1,2,8),(False,True)):
 assert m.source_request(y,uv,s,n,resize)==m.closed_request(y,uv,s,n,resize)==m.layout_request(y,uv,s,n,resize);acount+=1
print(json.dumps({'kind':'ARITHMETIC_RECHECK','height_cases':hcount,'allocation_cases':acount,'source_files_checked':source_checks,'codec_execution':False,'allocation_measurement':False},indent=2))
