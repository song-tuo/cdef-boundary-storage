from common import *
from collections import deque
out=[]
for R in range(1,11):
 for W in range(1,5):
  start=(0,(),0);seen={start};todo=deque([start]);peak=[0,0,0];witness=None
  while todo:
   nxt,active,copied=todo.popleft();live={r for r,c in active};top={r for r in live if r>0}
   if 0<nxt<R:top.add(nxt)
   bottom={r for r in live if r<R-1};tot=len(top)+len(bottom)
   peak=[max(peak[0],len(top)),max(peak[1],len(bottom)),max(peak[2],tot)]
   assert len(top)<=min(R-1,W+1) and len(bottom)<=min(R-1,W)
   # Any injective assignment of active rows to the W workers makes persistent
   # worker slots injective. Short-frame direct rows are injective independently.
   for ids in [range(len(active)),range(W-len(active),W)]:
    b=[worker if R-1>=W else r for worker,(r,c) in zip(ids,active) if r<R-1]
    assert len(b)==len(set(b)) and all(0<=i<min(R-1,W) for i in b)
   if tot==min(2*R-2,2*W+1):witness={'next_row':nxt,'active':active,'copy_mask':copied,'live_top':sorted(top),'live_bottom':sorted(bottom)}
   candidates=[]
   if nxt<R and len(active)<W:candidates.append((nxt+1,active+((nxt,False),),copied))
   for k,(r,done) in enumerate(active):
    if not done:
     a=list(active);a[k]=(r,True);candidates.append((nxt,tuple(a),copied|1<<r))
    elif r==0 or copied&(1<<(r-1)):candidates.append((nxt,active[:k]+active[k+1:],copied))
   for s in candidates:
    if s not in seen:seen.add(s);todo.append(s)
  assert peak==[min(R-1,W+1),min(R-1,W),min(2*R-2,2*W+1)] and witness is not None
  out.append({'R':R,'W':W,'states':len(seen),'peak_top':peak[0],'peak_bottom':peak[1],'peak_total':peak[2],'witness':witness,'pass':True})
save(ROOT/'results/theory_check.json',{'cases':out,'symmetry':'worker identities interchangeable for the bottom-slot injectivity property; schedule enumeration retains every abstract legal issue/copy/finish order','general_proof':'THEORY_CHECK.md'})
print('PASS',len(out),'finite parameter cases;',sum(x['states'] for x in out),'reachable abstract schedules')
