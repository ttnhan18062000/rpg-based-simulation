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
from src.engine.apply import ApplyPath
KILLS=collections.Counter(); ATT_ATTEMPT=collections.Counter()
_ag=ApplyPath.apply_generation
def ag(state, update, *a, **kw):
    try:
        for eid, upd in update.entity_updates.items():
            c=getattr(upd,"combat",None)
            if c is not None and getattr(c,"alive_set",None) is False and getattr(c,"outcome_kind",None) in ("KILL","DEFEAT"):
                v=state.entities.get(eid); atk=state.entities.get(getattr(c,"attacker_id",None))
                vf=(v.identity.properties or {}).get("faction_id") if v else None; vs=(v.identity.properties or {}).get("species_id") if v else None
                af=(atk.identity.properties or {}).get("faction_id") if atk else None
                KILLS[(af,vf,vs,str(c.outcome_kind))]+=1
    except Exception as ex: KILLS[("ERR",str(ex)[:40],None,None)]+=1
    return _ag(state, update, *a, **kw)
ApplyPath.apply_generation=staticmethod(ag)
for _ in range(TICKS): k.tick_once()
st=k.state
sp=collections.Counter(((e.identity.properties or {}).get("species_id"),(e.identity.properties or {}).get("faction_id"),str(e.identity.role)) for e in st.entities.values())
k.shutdown()
print("KL",json.dumps(dict(world=WORLD,seed=SEED,kills={"|".join(map(str,k_)):v for k_,v in KILLS.items()},roster={"|".join(map(str,k_)):v for k_,v in sp.items()})))
