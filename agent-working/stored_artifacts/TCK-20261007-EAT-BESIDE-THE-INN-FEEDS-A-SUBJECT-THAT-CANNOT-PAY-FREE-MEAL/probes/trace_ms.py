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

from src.engine.legality import LegalityServiceV2
from src.core.items import food_hunger_recovery
FOOD_IDS=lambda st:[n for n in st.resource_nodes.values() if food_hunger_recovery(n.yields_item)>0]
fregions=set(); entry={}; last={}; rows=[]; seen_dead=set(); stay=collections.defaultdict(int)
for _ in range(TICKS):
    k.tick_once(); st=k.state
    if not fregions:
        for n in FOOD_IDS(st):
            r=LegalityServiceV2.get_region_for_position(n.position,st)
            if r: fregions.add(r.id)
    for e in st.entities.values():
        alive=e.combat.alive and e.lifecycle.active
        r=LegalityServiceV2.get_region_for_position(e.navigation.position,st)
        rid=r.id if r else None
        if alive:
            last[e.id]=(rid,e.navigation.position,e.inventory.gold,getattr(e.task,"kind",None) if hasattr(e,"task") else None, (e.identity.properties or {}).get("faction_id"), str(e.identity.role), (e.identity.properties or {}).get("species_id"))
            if rid in fregions:
                entry.setdefault(e.id,st.tick); stay[e.id]+=1
        elif e.id not in seen_dead:
            seen_dead.add(e.id)
            c=e.lifecycle.passive_death_cause or e.lifecycle.death_reason; c=str(getattr(c,"value",c))
            lr=last.get(e.id)
            rows.append(dict(id=e.id,tick=st.tick,cause=c,last=lr,entered_tick=entry.get(e.id),ticks_in_food_region=stay.get(e.id,0)))
info={str(i):dict(faction=(k.state.entities[i].identity.properties or {}).get('faction_id'),ticks=v,alive=bool(k.state.entities[i].combat.alive and k.state.entities[i].lifecycle.active),entry=entry.get(i)) for i,v in stay.items()}
k.shutdown()
print("TR",json.dumps(dict(seed=SEED,info=info,fregions=sorted(fregions),deaths=rows,stay={str(i):v for i,v in stay.items()})))
