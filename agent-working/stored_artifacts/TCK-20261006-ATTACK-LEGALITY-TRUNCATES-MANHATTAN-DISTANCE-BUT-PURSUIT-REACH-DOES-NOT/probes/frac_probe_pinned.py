"""Fractional positions: who produces them, and what the attack/pursuit distance checks do with them.
usage: frac_probe.py <root> <world> <ticks> [seed]"""
import collections
import json
import sys
import traceback

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 42
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.core.updates import EntityUpdate
from src.engine.candidate_selector import MovementCandidateSelector as MCS
from src.core.governance import RuntimeMode
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.legality import LegalityServiceV2 as L
from src.engine.tactical import TacticalDecisionSystem as T
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

C = collections.Counter()
SRC = collections.Counter()          # fractional new_position writes, by producing call site
LAST_SRC = {}                        # entity id -> call site of its last fractional write
SAMPLES = {}


def frac(p):
    return p is not None and (p[0] != int(p[0]) or p[1] != int(p[1]))


_init = EntityUpdate.__init__


def init(self, *a, **k):
    _init(self, *a, **k)
    npos = self.new_position
    if frac(npos):
        site = "?"
        for fs in reversed(traceback.extract_stack(limit=12)[:-1]):
            if "/src/" in fs.filename and not fs.filename.endswith("core/updates.py"):
                site = f"{fs.filename.split('/src/')[-1]}:{fs.lineno}:{fs.name}"
                break
        SRC[site] += 1
        LAST_SRC[self.entity_id] = site
        SAMPLES.setdefault(site, npos)


EntityUpdate.__init__ = init

_ev = T.evaluate_entity_intent


def ev(state, entity, *a, **kw):
    r = _ev(state, entity, *a, **kw)
    pl = (r.task.payload_set or {}) if r is not None and r.task is not None else {}
    if pl.get("action") == "ATTACK":
        t = state.entities.get(pl.get("target_id"))
        if t is not None:
            d = abs(t.navigation.position[0] - entity.navigation.position[0]) + abs(t.navigation.position[1] - entity.navigation.position[1])
            C["attack_decisions"] += 1
            if d > 1:
                C["attack_decisions_float_dist_above_1"] += 1
            if frac(entity.navigation.position) or frac(t.navigation.position):
                C["attack_decisions_with_a_fractional_party"] += 1
    return r


T.evaluate_entity_intent = staticmethod(ev)
_re = MCS._target_in_attack_reach


def reach(entity, target):
    r = _re(entity, target)
    C["reach_checks"] += 1
    legal = L.get_manhattan_dist(entity.navigation.position, target.navigation.position) <= max(1, entity.combat.range) \
        if entity.combat.range > 1.5 else L.get_manhattan_dist(entity.navigation.position, target.navigation.position) <= 1
    if frac(entity.navigation.position) or frac(target.navigation.position):
        C["reach_checks_with_fractional_party"] += 1
    if legal != r:
        C["reach_disagrees_with_legality"] += 1
        C["reach_false_but_legality_true" if legal else "reach_true_but_legality_false"] += 1
    return r


MCS._target_in_attack_reach = staticmethod(reach)

class Pin(ResourceGovernor):
    def _get_indicated_mode(self, profile, signals): return RuntimeMode.NORMAL
    def force_mode(self, mode, status, current_tick): return None
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, SEED, context=ctx)
C["initial_fractional_entities"] = sum(1 for e in state.entities.values() if frac(e.navigation.position))
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED), governor=Pin(),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
ever = set(); seen = set(); maxfrac = 0
from src.engine.domain.core_actions import CoreActions
_es = CoreActions.execute_survival
def es(entity, action, current_tick):
    C[f"survival_action.{action}"] += 1
    return _es(entity, action, current_tick)
CoreActions.execute_survival = staticmethod(es)
try:
    for _ in range(TICKS):
        k.tick_once()
        nfrac = 0
        for e in k.state.entities.values():
            seen.add(e.id)
            if frac(e.navigation.position):
                ever.add(e.id); nfrac += 1
        maxfrac = max(maxfrac, nfrac)
    final = k.state
    C["max_fractional_entities_at_any_tick"] = maxfrac
    C["entities_ever_seen"] = len(seen)
    C["entities_alive_at_end"] = sum(1 for e in final.entities.values() if e.combat.alive and e.lifecycle.active)
    C["entities_dead_or_removed"] = len(seen) - C["entities_alive_at_end"]
    C["entities_total_final"] = len(final.entities)
    C["entities_ever_fractional"] = len(ever)
    C["entities_fractional_at_end"] = sum(1 for e in final.entities.values() if frac(e.navigation.position))
    by_src = collections.Counter(LAST_SRC.get(i, "no-recorded-write(initial/other)") for i in ever)
finally:
    k.shutdown()
import hashlib
dig = hashlib.sha256(json.dumps(sorted((e.id, round(e.navigation.position[0],3), round(e.navigation.position[1],3), round(e.combat.hp,2), e.combat.alive) for e in final.entities.values())).encode()).hexdigest()[:16]
print("DIGEST", dig)
print("FRAC", WORLD, SEED, TICKS, json.dumps(dict(sorted(C.items()))))
print("FRAC-WRITES-BY-SITE", json.dumps(dict(SRC.most_common())))
print("FRAC-ENTITIES-BY-LAST-SITE", json.dumps(dict(by_src.most_common())))
print("FRAC-SAMPLES", json.dumps({s: list(v) for s, v in SAMPLES.items()}))
