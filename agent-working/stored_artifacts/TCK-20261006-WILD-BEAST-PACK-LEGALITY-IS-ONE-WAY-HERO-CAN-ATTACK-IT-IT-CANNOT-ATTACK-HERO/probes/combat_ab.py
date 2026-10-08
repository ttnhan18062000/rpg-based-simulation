"""combat_ab.py <world> <ticks> <out.json>: deaths and attack counts, one world, audit_mode with the tick budget disabled.
BEFORE=1 restores forward-only legality and drops the five wild kinds from SPAWN_KIND_CATALOG_FACTION (the pre-batch behaviour)."""
import sys, json, os, collections
from tests.helpers.scenario import compile_world, DEFAULT_SEED, DEFAULT_FLAGS
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.engine.apply import ApplyPath
from src.engine.legality import LegalityServiceV2 as L
from src.platform.rng import DeterministicRNG
from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service
import src.systems.world_systems.generator as g
if os.environ.get("BEFORE"):
    for kd in ["wolf", "slime", "bear", "harpy", "golem"]: g.SPAWN_KIND_CATALOG_FACTION.pop(kd)
    def _old(a, t, c):  # pre-batch: forward-only, has_clean on the attacker
        svc = get_faction_semantics_service(); src, tf = get_faction_id_str(a), get_faction_id_str(t)
        if L._declares(svc.repo, src, tf): return bool(svc.is_hostile_compat(src, tf, c))
        return a.identity.faction != t.identity.faction
    L._attack_permitted = staticmethod(_old)
world, ticks, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
st = compile_world(world, DEFAULT_SEED)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=st, rng=DeterministicRNG(DEFAULT_SEED), flags={**DEFAULT_FLAGS, "audit_mode": True})
c = collections.Counter(); pairs = collections.Counter(); orig = ApplyPath.apply_generation
def fac(s, i):
    e = s.entities.get(i); return get_faction_id_str(e) if e is not None else None
def wrapped(prior, update, *a, **kw):
    for eid, eu in update.entity_updates.items():
        cb = eu.combat
        if cb is None: continue
        if cb.attacker_id is not None and (cb.damage_taken or 0) > 0:
            c["attacks"] += 1; pairs[f"{fac(prior, cb.attacker_id)}>{fac(prior, eid)}"] += 1
            if fac(prior, cb.attacker_id) == "wild_beast_pack": c["wild_attacker_hits"] += 1
        if cb.alive_set is False and eid in prior.entities and prior.entities[eid].combat.alive:
            c["deaths"] += 1; c["hazard_deaths" if cb.outcome_kind is None or (cb.hazard_damage or 0) > 0 else "combat_deaths"] += 1
            if fac(prior, eid) == "wild_beast_pack": c["wild_deaths"] += 1
    return orig(prior, update, *a, **kw)
ApplyPath.apply_generation = staticmethod(wrapped)
for _ in range(ticks): k.tick_once()
json.dump({"world": world, "ticks": ticks, "counts": dict(c), "pairs": dict(pairs), "final_entities": len(k._state.entities)}, open(out, "w"))
