from checks import *
rows=[]
for profile in ['asan','tsan']:
 counts=Counter();frames=Counter();violations=[]
 for line in (ROOT/'logs'/f'fpmt_{profile}_small.stderr').read_text().splitlines():
  if not line.startswith('{'):continue
  try:e=json.loads(line)
  except ValueError:continue
  counts[e.get('h1')]+=1
  if e.get('h1')=='frame_begin':frames[(e['rows'],e['workers'])]+=1
  if e.get('h1')=='violation':violations.append(e)
 rows.append({'profile':profile,'events':dict(counts),'frame_regimes':[{'R':r,'W':w,'frames':n} for (r,w),n in sorted(frames.items())],'violations':violations,'actual_MT_frames':sum(n for (r,w),n in frames.items() if w>1),'pass':counts['dispatch']==counts['release'] and counts['alloc']==counts['free'] and not violations and any(w>1 for r,w in frames)})
save(ROOT/'results/fpmt_path_coverage.json',rows);assert all(r['pass'] for r in rows)
print('Independent encoder CDEF multithread path reached in both sanitizer builds')
