from common import *
import shlex
rows=[]
for profile in ['asan','tsan']:
 b=ROOT/'builds'/f'hybrid_audit_fpmt_{profile}';tag='instrumentation_fpmt_'+profile;run(tag,['ar','-t',b/'libaom.a']);members=[m for m in (ROOT/'logs'/(tag+'.stdout')).read_text().splitlines() if m and not m.startswith('__.SYMDEF')];commands=json.loads((b/'compile_commands.json').read_text());cmds={}
 for r in commands:
  args=shlex.split(r['command'])
  if '-o' in args:cmds[Path(args[args.index('-o')+1]).name]=r['command']
 flag='-fsanitize='+{'asan':'address,undefined','tsan':'thread'}[profile];missing=[m for m in members if flag not in cmds.get(m,'')]
 rows.append({'profile':profile,'archive_members':len(members),'missing_instrumented_compile_command':missing,'pass':not missing})
save(ROOT/'results/fpmt_instrumentation_audit.json',rows);assert all(r['pass'] for r in rows);print(rows)
