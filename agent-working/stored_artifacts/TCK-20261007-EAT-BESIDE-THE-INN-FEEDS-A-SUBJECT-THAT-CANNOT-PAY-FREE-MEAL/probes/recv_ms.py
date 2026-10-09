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
from src.core.conservation import ResourceTransactionResolver as RTR
from src.core.items import food_hunger_recovery
LOG=[]; _r=RTR.resolve
def res(state, entity, intent, *a, **kw):
    out=_r(state, entity, intent, *a, **kw)
    try:
        if out.accepted and any(food_hunger_recovery(i.item_id)>0 for i in (intent.items_add or [])):
            LOG.append((state.tick, (entity.identity.properties or {}).get("faction_id"), entity.id, intent.source_kind, getattr(intent,"transfer_kind",None), intent.source_id, [(i.item_id,i.quantity) for i in intent.items_add]))
    except Exception as ex: LOG.append(("ERR",str(ex)[:50]))
    return out
RTR.resolve=staticmethod(res)
prevf={}; unexplained=[]
def foodq(e): return sum(i.quantity for i in e.inventory.items if food_hunger_recovery(i.item_id)>0)
for _ in range(TICKS):
    k.tick_once(); st0=k.state
    for e in st0.entities.values():
        q=foodq(e); p=prevf.get(e.id,0)
        if q>p:
            expl=[x for x in LOG if x[0]==st0.tick-1 or x[0]==st0.tick]
            mine=[x for x in expl if x[2]==e.id]
            if not mine: unexplained.append((st0.tick,(e.identity.properties or {}).get("faction_id"),e.id,p,q,e.navigation.position))
        prevf[e.id]=q
st=k.state
k.shutdown()
import collections as c
print("RC",json.dumps(dict(world=WORLD,seed=SEED,by_kind=dict(c.Counter((x[1],x[3],x[4]) for x in LOG if x[0]!="ERR" ).most_common(12)) if False else {"|".join(map(str,k_)):v for k_,v in c.Counter((x[1],x[3],x[4]) for x in LOG if x[0]!="ERR").items()},unexplained=unexplained[:12],first_town_council=[x for x in LOG if x[0]!="ERR" and x[1]=="town_council" and x[3]!="NODE"][:6])))
