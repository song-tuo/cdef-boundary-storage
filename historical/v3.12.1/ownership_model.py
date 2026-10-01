"""Exhaustively check legal dispatch/copy/filter schedules, independent of C slots."""
from pathlib import Path
import json,collections
root=Path(__file__).resolve().parents[1];results=[]
for rows in range(1,9):
    for workers in range(1,min(rows,4)+1):
        # State: next row, active tuple(row, copied), completed-copy bitset.
        start=(0,(),0);seen={start};todo=collections.deque([start]);peak=[0,0]
        while todo:
            nextrow,active,copied=todo.popleft();live={i for i,c in active}
            top={i for i in live if i>0}
            if nextrow and nextrow<rows:top.add(nextrow)
            bottom={i for i in live if i<rows-1}
            peak=[max(peak[0],len(top)),max(peak[1],len(bottom))]
            assert len(top)<=min(rows-1,workers+1)
            assert len(bottom)<=min(rows-1,workers)
            candidates=[]
            if nextrow<rows and len(active)<workers:
                candidates.append((nextrow+1,active+((nextrow,False),),copied))
            for k,(i,done) in enumerate(active):
                if not done:
                    a=list(active);a[k]=(i,True);candidates.append((nextrow,tuple(a),copied|(1<<i)))
                elif not i or copied&(1<<(i-1)):
                    candidates.append((nextrow,active[:k]+active[k+1:],copied))
            for state in candidates:
                if state not in seen:seen.add(state);todo.append(state)
        assert peak==[min(rows-1,workers+1),min(rows-1,workers)]
        results.append(dict(rows=rows,workers=workers,states=len(seen),peak_top=peak[0],peak_bottom=peak[1],pass_gate=True))
ring=dict(workers=2,rows=5,modulus=3,schedule=['dispatch 0','dispatch 1','copy 0','copy 1','finish 0','dispatch 2','copy 2','finish 2','dispatch 3'],live_top_boundaries=[1,3,4],collision=[1,4],same_slot=1)
assert ring['collision'][0]%3==ring['collision'][1]%3
(root/'results/ownership_schedule_model.json').write_text(json.dumps(dict(exhaustive=results,fixed_ring_counterexample=ring),indent=2)+'\n')
print('PASS',sum(x['states'] for x in results),'states in',len(results),'finite models; fixed row modulo counterexample confirmed')
