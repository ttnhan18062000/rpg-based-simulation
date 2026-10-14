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
EATF = collections.Counter(); C = collections.Counter(); PEND = {}; WALK = []; SEEN_WALK = set(); NA_ENT = collections.defaultdict(set)
from src.engine.domain.core_actions import CoreActions
_es = CoreActions.execute_survival
def food_carried(e):
    try:
        from src.core.items import food_hunger_recovery
        return sum(s.quantity for s in e.inventory.items if food_hunger_recovery(s.item_id) > 0)
    except ImportError:
        return sum(s.quantity for s in e.inventory.items if s.item_id in ("bread", "travel_ration", "wild_berries"))
def es(entity, action, current_tick):
    if action == "EAT":
        carried = food_carried(entity)
        C["eat_executed"] += 1
        if carried: EATF[(entity.identity.properties or {}).get("faction_id")] += 1
        C["eat_executed.carried" if carried else ("eat_executed.nocarry.gold_lt5" if entity.inventory.gold < 5 else "eat_executed.nocarry.gold_ge5")] += 1
        PEND[entity.id] = (current_tick, entity.biological.hunger, entity.inventory.gold, carried)
    return _es(entity, action, current_tick)
CoreActions.execute_survival = staticmethod(es)
from src.ai.goals.scorers import EatScorer
_sc = EatScorer.score
def score(self, entity, st):
    r = _sc(self, entity, st)
    a = getattr(r, "need_access", None)
    if a is not None and entity.biological.hunger >= 60.0:
        C[f"hot.access.{a.value}"] += 1; NA_ENT[f"access.{a.value}"].add(entity.id)
        if getattr(r, "no_open_step", False): C["hot.no_open_step"] += 1; NA_ENT["no_open_step"].add(entity.id)
        step = getattr(r, "opening_step", None)
        if step is not None:
            C[f"hot.opening_step.{step.value}"] += 1; NA_ENT[f"step.{step.value}"].add(entity.id)
            if entity.id not in SEEN_WALK and r.target_pos is not None:
                SEEN_WALK.add(entity.id)
                WALK.append(abs(entity.navigation.position[0] - r.target_pos[0]) + abs(entity.navigation.position[1] - r.target_pos[1]))
    return r
EatScorer.score = score
ENTERED = {}; FREGIONS = set(); recov = 0; deplete = 0
GATHF = collections.Counter(); PREVB = {}; HUNGER_LAST = {}
DEATH_TICK = {}; dead = {}; GOLD = {}; R = {}; prev_charges = None; food_ids = set(); dry_ticks = 0; dry_trans = 0; was_dry = False; harvested = 0; regen = 0
def is_food(n):
    try:
        from src.core.items import food_hunger_recovery
        return food_hunger_recovery(n.yields_item) > 0
    except ImportError:
        return False
try:
    for _ in range(TICKS):
        k.tick_once(); st = k.state
        fn = {i: n for i, n in st.resource_nodes.items() if is_food(n)}
        if fn:
            cur = {i: n.remaining_charges for i, n in fn.items()}
            if prev_charges is not None:
                for i, c in cur.items():
                    d = c - prev_charges.get(i, c)
                    if d < 0: harvested += -d
                    elif d > 0: regen += d
                for i, c in cur.items():
                    p = prev_charges.get(i, c)
                    if p > 0 and c == 0: deplete += 1
                    if p == 0 and c > 0: recov += 1
            prev_charges = cur
            if not FREGIONS:
                from src.engine.legality import LegalityServiceV2
                for n in fn.values():
                    r_ = LegalityServiceV2.get_region_for_position(n.position, st)
                    if r_ is not None: FREGIONS.add(r_.id)
            dry = all(c == 0 for c in cur.values())
            dry_ticks += dry; dry_trans += (dry and not was_dry); was_dry = dry
        for eid, (t, h0, g0, carried) in list(PEND.items()):
            if st.tick > t:
                e = st.entities.get(eid)
                if e is not None:
                    dropped = e.biological.hunger < h0 - 5
                    if dropped and not carried and g0 < 5: C["FREE_MEAL"] += 1   # hunger fell with no food carried and no gold to pay
                    C["eat_effect.dropped" if dropped else "eat_effect.none"] += 1
                    if carried: C["carried_meals_delivered" if (food_carried(e) < carried) else "carried_meal_item_kept"] += 1
                del PEND[eid]
        if FREGIONS:
            from src.engine.legality import LegalityServiceV2
            for e in st.entities.values():
                if e.id not in dead and e.combat.alive and e.lifecycle.active and e.id not in ENTERED:
                    r_ = LegalityServiceV2.get_region_for_position(e.navigation.position, st)
                    if r_ is not None and r_.id in FREGIONS: ENTERED[e.id] = e.inventory.gold
        for e in st.entities.values():
            if e.combat.alive and e.lifecycle.active:
                HUNGER_LAST[e.id] = e.biological.hunger
                b_ = food_carried(e); fid_ = (e.identity.properties or {}).get("faction_id")
                if b_ > PREVB.get(e.id, 0): GATHF[fid_] += b_ - PREVB.get(e.id, 0)
                PREVB[e.id] = b_
            if e.id not in dead and e.combat.alive and e.lifecycle.active: GOLD[e.id] = e.inventory.gold
            if e.id not in dead and not (e.combat.alive and e.lifecycle.active):
                c = e.lifecycle.passive_death_cause or e.lifecycle.death_reason
                dead[e.id] = str(getattr(c, "value", c)); DEATH_TICK[e.id] = st.tick
        if st.tick in (1000, 1100, 2500, 4000, 5000):
            R[f"alive_t{st.tick}"] = sum(1 for e in st.entities.values() if e.combat.alive and e.lifecycle.active)
finally:
    k.shutdown()
end = k.state
carried_end = sum(food_carried(e) for e in end.entities.values())
carried_alive = sum(food_carried(e) for e in end.entities.values() if e.combat.alive and e.lifecycle.active)
dig = hashlib.sha256(json.dumps(sorted((e.id, round(e.navigation.position[0], 3), round(e.navigation.position[1], 3), round(e.combat.hp, 2), e.combat.alive, round(e.biological.hunger, 2), e.inventory.gold) for e in end.entities.values()) + sorted(dead.items())).encode()).hexdigest()[:16]
starved = [i for i, c in dead.items() if c == "STARVATION"]
out = dict(R, starved_broke=sum(1 for i in starved if GOLD.get(i, 0) < 5), starved_could_pay=sum(1 for i in starved if GOLD.get(i, 0) >= 5), deaths=len(dead), digest=dig,
           food_harvested=harvested, food_regrown=regen, food_carried_end=carried_end, food_carried_end_alive=carried_alive, food_nodes=len([1 for n in end.resource_nodes.values() if is_food(n)]),
           hazard_deaths_starving=sum(1 for i, c in dead.items() if c == 'HAZARD' and HUNGER_LAST.get(i, 0) >= 95.0),
           hunger_related_deaths=sum(1 for i, c in dead.items() if c == 'STARVATION' or (c == 'HAZARD' and HUNGER_LAST.get(i, 0) >= 95.0)),
           deaths_per_1000=[sum(1 for t_ in DEATH_TICK.values() if 1000*b < t_ <= 1000*(b+1)) for b in range(TICKS // 1000 + 1)],
           starved_per_1000=[sum(1 for i, t_ in DEATH_TICK.items() if dead[i] == 'STARVATION' and 1000*b < t_ <= 1000*(b+1)) for b in range(TICKS // 1000 + 1)],
           gathered_by_faction=dict(GATHF), carried_eats_by_faction=dict(EATF),
           food_depletions=deplete, food_recoveries=recov, entered_food_region=len(ENTERED), entered_broke=sum(1 for g in ENTERED.values() if g < 5),
           hazard_deaths_after_entering=sum(1 for i, c in dead.items() if c == 'HAZARD' and i in ENTERED),
           hazard_deaths_after_entering_broke=sum(1 for i, c in dead.items() if c == 'HAZARD' and i in ENTERED and ENTERED[i] < 5),
           starved_after_entering=sum(1 for i, c in dead.items() if c == 'STARVATION' and i in ENTERED),
           node_dry_ticks=dry_ticks, node_dry_transitions=dry_trans, walk_median=(statistics.median(WALK) if WALK else None), walk_n=len(WALK),
           **{f"ent.{a}": len(v) for a, v in NA_ENT.items()}, **dict(C), **{f"d_{c}": n for c, n in collections.Counter(dead.values()).items()})
print("MS", json.dumps(dict(world=WORLD, seed=SEED, label=LABEL, **out)))
