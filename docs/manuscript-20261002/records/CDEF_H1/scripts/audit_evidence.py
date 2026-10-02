from checks import *
import difflib,shlex,tarfile
reports=[]
for variant,profile in [('hybrid','debug'),('hybrid','asan'),('hybrid','tsan'),('hybrid_audit','asan'),('hybrid_audit','tsan')]:
 b=ROOT/'builds'/f'{variant}_{profile}';tag=f'instrumentation_{variant}_{profile}';run(tag,['ar','-t',b/'libaom.a']);members=[l for l in (ROOT/'logs'/(tag+'.stdout')).read_text().splitlines() if l and not l.startswith('__.SYMDEF')];commands=json.loads((b/'compile_commands.json').read_text());byobj={}
 for c in commands:
  words=shlex.split(c['command']);obj=words[words.index('-o')+1] if '-o' in words else '';byobj[Path(obj).name]=c
 missing=[m for m in members if m not in byobj];checks=[]
 for m in members:
  c=byobj.get(m,{});text=c.get('command','');required={'debug':'-g','asan':'-fsanitize=address,undefined','tsan':'-fsanitize=thread'}[profile];checks.append({'member':m,'source':c.get('file'),'required_flag':required,'present':required in text,'assertions_enabled':'-DNDEBUG' not in text})
 reports.append({'variant':variant,'profile':profile,'archive_members':len(members),'missing_compile_commands':missing,'all_required_flags':not missing and all(c['present'] for c in checks),'all_assertions_enabled':all(c['assertions_enabled'] for c in checks),'objects':checks})
save(ROOT/'results/instrumentation_audit.json',reports)
for v in ['type_fix','dual_token','hybrid']:
 for mode in ['audit','account']:
  out=[];a=ROOT/'src'/v;b=ROOT/'src'/(v+'_'+mode)
  for p in sorted(b.rglob('*')):
   if not p.is_file():continue
   rel=p.relative_to(b);old=a/rel
   if not old.exists() or p.read_bytes()!=old.read_bytes():
    try:out+=list(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],p.read_text().splitlines(True),fromfile=str(Path(v)/rel),tofile=str(Path(v+'_'+mode)/rel)))
    except UnicodeDecodeError:raise
  (ROOT/'patches'/f'{v}_to_{mode}.patch').write_text(''.join(out))
# Verify old copied source trees stayed unchanged; never write to them.
lineage=json.loads((ROOT/'inputs/source_input_manifest.json').read_text());oldmismatch=[x['original'] for x in lineage if sha(x['original'])!=x['sha256']];save(ROOT/'results/prior_source_preservation.json',{'verified_files':len(lineage),'mismatches':oldmismatch,'read_only':True})
seal=json.loads((ROOT/'protocol/IMPLEMENTATION_SEAL.json').read_text());changed=[x['path'] for x in seal['files'] if sha(ROOT/x['path'])!=x['sha256']];save(ROOT/'results/seal_recheck.json',{'verified_files':len(seal['files']),'changed':changed})
# Compare the whole clean source to official archive; distinguish inherited packaging-only files.
with tarfile.open(ROOT/'upstream/v3.12.1.tar') as tf:
 members={m.name:tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
for v in ['type_fix','dual_token','hybrid']:
 diff=[];missing=[]
 for name,data in members.items():
  p=ROOT/'src'/v/name
  if not p.exists():missing.append(name)
  elif p.read_bytes()!=data:diff.append(name)
 extras=[str(p.relative_to(ROOT/'src'/v)) for p in (ROOT/'src'/v).rglob('*') if p.is_file() and str(p.relative_to(ROOT/'src'/v)) not in members]
 save(ROOT/'results'/f'{v}_official_diff.json',{'official_commit':'10aece4157eb79315da205f39e19bf6ab3ee30d0','official_files':len(members),'changed':diff,'missing':missing,'extra_packaging_files':extras})
print('instrumented member validation',[(r['profile'],r['archive_members'],r['all_required_flags']) for r in reports]);print('seal changed',changed,'old source changed',oldmismatch)
