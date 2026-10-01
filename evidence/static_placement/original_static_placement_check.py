# Independent event-model check (written from the paper's contract, not from the author's script).
# Rows issued in order; <= W active; active row: dispatched -> copied; may return iff copied and
# (i==0 or row i-1 copied). Row i (nonfinal) copies T_{i+1} and B_i at its copy event.
# T_j live from C_{j-1} to F_j ; B_i live from C_i to F_i.
import itertools, sys
from collections import deque

def live_set(R, q, active):
    act = dict(active)                      # row -> copied flag
    copied = lambda i: (i < q and i not in act) or act.get(i, False)
    returned = lambda i: i < q and i not in act
    L = set()
    for i in range(R - 1):                  # nonfinal rows
        if copied(i):
            if not returned(i + 1): L.add(('T', i + 1))
            if i in act:            L.add(('B', i))
    return frozenset(L)

def explore(R, W):
    start = (0, frozenset())
    seen, dq, livesets = {start}, deque([start]), set()
    while dq:
        q, active = dq.popleft()
        livesets.add(live_set(R, q, active))
        act = dict(active)
        nxt = []
        if q < R and len(act) < W:                       # dispatch
            nxt.append((q + 1, active | {(q, False)}))
        for i, c in act.items():
            if not c:                                    # copy
                nxt.append((q, (active - {(i, False)}) | {(i, True)}))
            else:                                        # return (needs predecessor copy)
                pred_ok = i == 0 or (i - 1 < q and (i - 1 not in act or act[i - 1]))
                if pred_ok:
                    nxt.append((q, active - {(i, True)}))
        for s in nxt:
            if s not in seen:
                seen.add(s); dq.append(s)
    return livesets

def chromatic(vertices, edges, lb=0):
    n = len(vertices)
    if len(edges) == n * (n - 1) // 2: return n
    vs = sorted(vertices, key=lambda v: -sum(v in e for e in edges))
    adj = {v: set() for v in vs}
    for a, b in edges: adj[a].add(b); adj[b].add(a)
    for k in range(lb, len(vs) + 1):
        col = {}
        def bt(idx):
            if idx == len(vs): return True
            v = vs[idx]
            used = max(col.values(), default=-1)
            for c in range(min(k, used + 2)):
                if all(col.get(u) != c for u in adj[v]):
                    col[v] = c
                    if bt(idx + 1): return True
                    del col[v]
            return False
        if bt(0): return k
    return len(vs)

ok = True
for W in range(1, 5):
    for R in range(1, 11):
        LS = explore(R, W)
        K = 0 if R == 1 else min(2 * R - 2, 2 * W + 1)
        peak = max(len(s) for s in LS)
        topcap = 0 if R == 1 else min(R - 1, W + 1)
        botcap = 0 if R == 1 else min(R - 1, W)
        simul = any(sum(x[0]=='T' for x in s) == topcap and sum(x[0]=='B' for x in s) == botcap for s in LS)
        strips = {('T', j) for j in range(1, R)} | {('B', i) for i in range(R - 1)}
        conf = set()
        for s in LS:
            for a, b in itertools.combinations(sorted(s), 2): conf.add((a, b))
        allpairs = len(conf) == len(strips) * (len(strips) - 1) // 2
        chi = chromatic(strips, conf, peak) if strips else 0
        # static placement need = chromatic number of union conflict graph
        exp_static = (2 * R - 2) if (W >= 2 or R <= 2) else min(2 * R - 2, 3)
        good = peak == K and simul and chi == exp_static and (allpairs == (W >= 2 or R <= 2))
        ok &= good
        print(f"W={W} R={R:2d} states_livesets={len(LS):4d} peak={peak:2d} K={K:2d} simul={simul} "
              f"all_pairs_conflict={allpairs} static_slots={chi:2d} expected={exp_static:2d} {'OK' if good else 'FAIL'}")
print("ALL OK" if ok else "SOME FAIL")
