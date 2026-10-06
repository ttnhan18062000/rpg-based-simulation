"""zones.py <world> <ticks> <out.jsonl>: one row per death with the tick-start position (the one the trauma block uses), the set of regions
containing it by inclusive bounds, the region the unified lookup credits, victim and killer faction/species/role/spawn_region, the combat
outcome kind, hazard damage in the lethal update, and the passive death cause.

TAKEN UNDER audit_mode WITH THE TICK BUDGET DISABLED (max_tick_budget_ms=1e9). Outside audit_mode the kernel drops work when wall-clock compute
time exceeds the budget (kernel.py:466-469), so slower worlds are not reproducible run to run (TCK-20261005-TICK-BUDGET-THROTTLE-...).
Deaths are captured by wrapping ApplyPath.apply_generation and reading the refined update it is about to commit (alive_set False on a
previously alive entity). Rows are written as they happen. Run from a worktree root: PYTHONPATH=. python zones.py ..."""
import sys, json
from tests.helpers.scenario import compile_world, DEFAULT_SEED, DEFAULT_FLAGS
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.engine.apply import ApplyPath
from src.engine.spatial_query import SpatialQueryService
from src.platform.rng import DeterministicRNG
from src.content_semantics.faction import get_faction_id_str
import os
import src.systems.world_systems.generator as _g
if os.environ.get('NOFIX'): _g.SPAWN_KIND_CATALOG_FACTION.clear(); _g.EntityGenerator.free_spawn_position = lambda self, pos, state: pos
world, ticks, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
st = compile_world(world, DEFAULT_SEED)
prof = PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9})
k = Kernel(profile=prof, state=st, rng=DeterministicRNG(DEFAULT_SEED), flags={**DEFAULT_FLAGS, "audit_mode": True})
bounds = {r: g.bounds for r, g in st.regions.items()}
f = open(out, "w"); f.write(json.dumps({"world": world, "ticks": ticks, "audit_mode": True, "max_tick_budget_ms": 1e9, "bounds": {r: list(b) for r, b in bounds.items()}, "hazard_level": {r: g.hazard_level for r, g in st.regions.items()}, "hazard_kind": {r: g.hazard_kind for r, g in st.regions.items()}}) + "\n")
def who(s, eid):
    e = s.entities.get(eid)
    if e is None: return None
    p = getattr(e.identity, "properties", {}) or {}
    return {"id": eid, "faction": get_faction_id_str(e), "species": p.get("species_id"), "role": str(e.kind), "spawn_region": p.get("spawn_region")}
orig = ApplyPath.apply_generation
last_hit = {}  # victim id -> (tick, attacker who) for the most recent attacker damage seen in a committed update
def wrapped(prior_state, update, *a, **kw):
    for eid, eu in update.entity_updates.items():
        c0 = eu.combat
        if c0 is not None and c0.attacker_id is not None and (c0.damage_taken or 0) > 0:
            last_hit[eid] = (prior_state.tick, who(prior_state, c0.attacker_id))
    for eid, eu in update.entity_updates.items():
        c = eu.combat
        if c is not None and c.alive_set is False:
            e = prior_state.entities.get(eid)
            if e is not None and e.combat.alive:
                x, y = e.navigation.position[0], e.navigation.position[1]
                hits = sorted(r for r, (a_, b_, c_, d_) in bounds.items() if a_ <= x <= c_ and b_ <= y <= d_)
                cr = SpatialQueryService.get_region_at(prior_state, (x, y))
                f.write(json.dumps({"tick": prior_state.tick, "pos": [float(x), float(y)], "zone": hits, "credited": cr.id if cr else None,
                    "victim": who(prior_state, eid), "killer": who(prior_state, c.attacker_id) if c.attacker_id is not None else None,
                    "last_hit": ({"tick": last_hit[eid][0], "ago": prior_state.tick - last_hit[eid][0], "attacker": last_hit[eid][1]} if eid in last_hit else None),
                    "outcome": c.outcome_kind, "hazard_damage": c.hazard_damage, "damage_taken": c.damage_taken,
                    "death_reason": str(getattr(e.lifecycle, "death_reason", None)),
                    "passive": str(getattr(e.lifecycle, "passive_death_cause", None))}) + "\n"); f.flush()
    return orig(prior_state, update, *a, **kw)
ApplyPath.apply_generation = staticmethod(wrapped)
initial_ids = set(st.entities)
seen_ids = set(initial_ids)
for t in range(ticks):
    k.tick_once()
    for e in k._state.entities.values():  # spawn record: first tick an entity id is seen, with its position and containing regions
        if e.id not in seen_ids:
            seen_ids.add(e.id)
            if t >= 0 and e.id not in initial_ids:
                x_, y_ = e.navigation.position[0], e.navigation.position[1]
                w_ = who(k._state, e.id) or {}
                if True:
                    pr_ = dict(getattr(e.identity, "properties", {}) or {})
                    f.write(json.dumps({"spawn": t + 1, "pos": [float(x_), float(y_)], "who": w_, "faction_enum": str(getattr(e.identity, "faction", None)), "props": {k_: str(v_)[:60] for k_, v_ in pr_.items() if k_ in ("faction_id", "species_id", "population_id", "spawn_region", "lair_place_id", "camp_id", "spawned_by", "origin", "raid_id")}, "prop_keys": sorted(pr_)[:25], "zone": sorted(r for r, (a_, b_, c_, d_) in bounds.items() if a_ <= x_ <= c_ and b_ <= y_ <= d_)}) + "\n"); f.flush()
    if (t + 1) % 100 == 0:  # real per-region trauma, so a replay of the producer can be checked against it
        f.write(json.dumps({"cp": t + 1, "trauma": {r: round(g.trauma_score, 4) for r, g in k._state.regions.items()}}) + "\n"); f.flush()
k.shutdown(); f.write(json.dumps({"final": True, "ticks": ticks}) + "\n"); f.close()
