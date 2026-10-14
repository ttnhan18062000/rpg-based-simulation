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

from src.ai.goals.scorers import EatScorer
from src.core.items import food_hunger_recovery
from src.engine.legality import LegalityServiceV2
from src.engine.domain.core_actions import CoreActions
LAST={}; _sc=EatScorer.score
def score(self, entity, st):
    r=_sc(self, entity, st); LAST[entity.id]=(st.tick, round(r.utility,1), getattr(getattr(r,"opening_step",None),"value",None), getattr(r,"target_pos",None), getattr(getattr(r,"need_access",None),"value",None), getattr(r,"no_open_step",False)); return r
EatScorer.score=score
EATF=collections.Counter(); _es=CoreActions.execute_survival
def es(entity, action, tick):
    if action=="EAT" and any(food_hunger_recovery(x.item_id)>0 for x in entity.inventory.items): EATF[(entity.identity.properties or {}).get("faction_id")]+=1
    return _es(entity, action, tick)
CoreActions.execute_survival=staticmethod(es)
GATHF=collections.Counter(); prevb={}; haz=[]; log=[]; died={}
def berries(e): return sum(x.quantity for x in e.inventory.items if food_hunger_recovery(x.item_id)>0)
for _ in range(TICKS):
    k.tick_once(); st=k.state
    if st.tick%100==0: haz.append((st.tick, st.regions["trading_hometown"].hazard_level, st.regions["trading_hometown"].calamity_intensity, st.regions["trading_hometown"].trauma_score))
    for e in st.entities.values():
        fid=(e.identity.properties or {}).get("faction_id"); b=berries(e)
        if b>prevb.get(e.id,0): GATHF[fid]+=b-prevb.get(e.id,0)
        prevb[e.id]=b
        alive=e.combat.alive and e.lifecycle.active
        if not alive:
            if e.id not in died:
                died[e.id]=st.tick
                if fid=="town_council": log.append(("DEAD",st.tick,e.id,str(e.lifecycle.passive_death_cause or e.lifecycle.death_reason)))
            continue
        if fid=="town_council" and e.inventory.gold<5 and e.biological.hunger>=50 and st.tick%50==0:
            r=LAST.get(e.id); reg=LegalityServiceV2.get_region_for_position(e.navigation.position,st)
            log.append((st.tick,e.id,round(e.biological.hunger),e.combat.hp,e.navigation.position,reg.id if reg else None,e.navigation.target,e.navigation.movement_mode.name if e.navigation.movement_mode else None,e.task.work_kind,sorted(e.task.payload)[:3],r))
k.shutdown()
print("TR2",json.dumps(dict(seed=SEED,gather_by_faction=dict(GATHF),eat_carried_by_faction=dict(EATF),hazard_trading_hometown=haz,log=log),default=str))
