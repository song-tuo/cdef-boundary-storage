from collections import deque
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def check(R,W):
 tc=min(R-1,W+1);bc=min(R-1,W);seen={(0,())};todo=deque(seen);terminal=0;blocked=0
 while todo:
  q,act=todo.popleft();d=dict(act)
  tops={j for j in d if j>0}|({q} if 0<q<R else set());bots={j for j in d if j<R-1}
  tm={(j-1)%tc:j for j in tops};bm={j%bc:j for j in bots}
  assert len(tm)==len(tops) and len(bm)==len(bots)
  nxt=[]
  if q<R and len(d)<W:
   if q==R-1 or (q%tc not in tm and q%bc not in bm):
    nxt.append((q+1,tuple(sorted([*act,(q,False)]))))
   else:blocked+=1
  for i,copied in act:
   if not copied:nxt.append((q,tuple((j,True if j==i else c) for j,c in act)))
   elif i==0 or (i-1<q and d.get(i-1,True)):
    nxt.append((q,tuple((j,c) for j,c in act if j!=i)))
  if not nxt:
   assert q==R and not act,('deadlock',R,W,q,act)
   terminal+=1
  for n in nxt:
   if n not in seen:seen.add(n);todo.append(n)
 assert terminal
 return dict(R=R,W=W,states=len(seen),capacity_blocked_states=blocked,no_alias=True,no_deadlock=True)
rows=[check(R,W) for R in range(1,11) for W in range(1,5)]
(ROOT/'results/ring_model.json').write_text(json.dumps(rows,indent=2)+'\n')
print('PASS',len(rows),'configurations;',sum(r['states'] for r in rows),'states')
