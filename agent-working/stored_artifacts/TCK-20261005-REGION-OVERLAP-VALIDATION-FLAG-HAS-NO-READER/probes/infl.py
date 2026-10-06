import sys, collections
from tests.helpers.scenario import compile_world, DEFAULT_SEED, DEFAULT_FLAGS
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.world.influence import FactionInfluenceService as F

world=sys.argv[1]; ticks=int(sys.argv[2])
calls=[]; orig=F.process_influence_shift
def wrap(state, deaths):
    r=orig(state, deaths)
    wu=getattr(r,"world_updates",{}) or {}
    calls.append((state.tick, [(d.id,d.kind,str(getattr(d.identity,"faction_id",None))) for d in deaths],
                  {k:(getattr(v,"influence_set",None),getattr(v,"owner_faction_id_set",None)) for k,v in wu.items()}))
    return r
F.process_influence_shift=staticmethod(wrap)
st=compile_world(world, DEFAULT_SEED)
k=Kernel(profile=PROD_SMALL,state=st,rng=DeterministicRNG(DEFAULT_SEED),flags=dict(DEFAULT_FLAGS))
infl0={r:(g.influence,str(g.owner_faction_id)) for r,g in st.regions.items()}
maxinfl=collections.defaultdict(float); owners=collections.defaultdict(set)
for t in range(ticks):
    k.tick_once()
    for r,g in k._state.regions.items():
        maxinfl[r]=max(maxinfl[r],abs(g.influence)); owners[r].add(str(g.owner_faction_id))
fin=k._state; k.shutdown()
print("world",world,"ticks",ticks)
print("process_influence_shift calls:",len(calls),"deaths passed:",sum(len(c[1]) for c in calls))
eff=[c for c in calls if c[2]]
print("calls returning non-empty world_updates:",len(eff))
print("first 3 calls:",calls[:3])
print("start influence/owner:",infl0)
print("max |influence| seen:",dict(maxinfl))
print("owners seen:",{r:sorted(v) for r,v in owners.items()})
print("final influence:",{r:(round(g.influence,2),str(g.owner_faction_id)) for r,g in fin.regions.items()})
