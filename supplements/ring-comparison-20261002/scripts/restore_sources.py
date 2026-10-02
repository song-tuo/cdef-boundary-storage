"""Reconstruct the two trees from the unmodified v3.12.1 baseline."""
from pathlib import Path
import argparse, subprocess, shutil, json,hashlib
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
assert not a.destination.exists(), 'Choose a fresh destination; no files are overwritten.'
assert (a.baseline/'av1/common/thread_common.c').is_file()
m=json.loads((root/'protocol/source_manifest.json').read_text())
for v in ['token','ring']:
 dst=a.destination/v;shutil.copytree(a.baseline,dst)
 patches=['baseline_to_type_fix.patch','type_fix_to_token.patch',f'token_to_{v}_with_optional_diagnostics.patch']
 for n in patches:
  with (root/'patches'/n).open('rb') as f:subprocess.run(['patch','-p1','--batch'],cwd=dst,stdin=f,check=True)
 for f in ['av1/common/alloccommon.c','av1/common/thread_common.c','av1/common/thread_common.h']:
  assert hashlib.sha256((dst/f).read_bytes()).hexdigest()==m[f'src/{v}/{f}'],f
print('Both reconstructed implementation trees match the measured core source hashes.')
