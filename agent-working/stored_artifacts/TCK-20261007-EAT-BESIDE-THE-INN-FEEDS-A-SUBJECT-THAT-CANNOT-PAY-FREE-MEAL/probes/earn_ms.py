"""Decision-27 / free-meal pinned measurement. usage: forage_ms.py <root> <world> <ticks> <seed> [label]
Pinned NORMAL governor + audit_mode + budget off + LocalSequentialExecutor. Counters degrade gracefully on the base arm (no opening steps)."""
import collections, hashlib, json, os, statistics, sys
ROOT, WORLD, TICKS, SEED = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); LABEL = sys.argv[5] if len(sys.argv) > 5 else ""
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.governance import RuntimeMode
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
class Pin(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals): return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick): return None
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED), governor=Pin(),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
EATF = collections.Counter(); 
prev={}; inflow=collections.Counter(); ever=set(); first={}
roster={e.id:((e.identity.properties or {}).get("faction_id"),str(e.identity.role)) for e in k.state.entities.values()}
start={e.id:e.inventory.gold for e in k.state.entities.values()}
for _ in range(TICKS):
    k.tick_once(); st=k.state
    for e in st.entities.values():
        g=e.inventory.gold; p=prev.get(e.id,start.get(e.id,g))
        if g>p and roster.get(e.id,(None,))[0]=="town_council": inflow[(roster[e.id][1],)]+=g-p; ever.add(e.id)
        prev[e.id]=g
bl={}
for b in k.state.buildings.values(): bl[b.kind]=bl.get(b.kind,0)+1
k.shutdown()
tc=[i for i,(f,_) in roster.items() if f=="town_council"]
print("EB",json.dumps(dict(world=WORLD,seed=SEED,town_council=len(tc),start_gold_ge5=sum(1 for i in tc if start[i]>=5),ever_gained_gold=len(ever),inflow={k_[0]:v for k_,v in inflow.items()},buildings=bl)))
