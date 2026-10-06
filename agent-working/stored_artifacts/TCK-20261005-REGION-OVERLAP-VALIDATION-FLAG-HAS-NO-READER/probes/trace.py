import sys, json, collections
from tests.helpers.scenario import compile_world, DEFAULT_SEED, DEFAULT_FLAGS
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.engine.world_dynamics import WorldDynamicsSystem as W
world=sys.argv[1]; ticks=int(sys.argv[2]); out=sys.argv[3]
calls=[]
orig=W._get_region_for_pos
def wrap(state,pos):
    r=orig(state,pos)
    ln=sys._getframe(1).f_lineno
    calls.append({"tick":state.tick,"line":ln,"pos":[float(pos[0]),float(pos[1])],"returned":r.id if r else None,
                  "bounds_hits":[g.id for g in state.regions.values() if g.bounds[0]<=pos[0]<g.bounds[2] and g.bounds[1]<=pos[1]<g.bounds[3]]})
    return r
W._get_region_for_pos=staticmethod(wrap)
st=compile_world(world,DEFAULT_SEED)
k=Kernel(profile=PROD_SMALL,state=st,rng=DeterministicRNG(DEFAULT_SEED),flags=dict(DEFAULT_FLAGS))
tr_prev={r:g.trauma_score for r,g in st.regions.items()}; deltas=[]
for t in range(ticks):
    k.tick_once(); s=k._state
    d={r:round(g.trauma_score-tr_prev[r],4) for r,g in s.regions.items() if abs(g.trauma_score-tr_prev[r])>0.5}
    if d: deltas.append({"tick_end":s.tick,"delta":d})
    tr_prev={r:g.trauma_score for r,g in s.regions.items()}
k.shutdown()
json.dump({"calls":calls,"deltas":deltas},open(out,"w"))
print("done",len(calls),"calls",len(deltas),"tick-deltas")
