"""Per tactical decision in the campaign episode: did the entity perceive a live hostile, was one within attack reach,
and what did it choose?  Read-only; same episode as the combat_initiated test (seed 42, 70 ticks).

usage: decision_opportunity.py <root>   (cwd is set to <root>; content seeds from the cwd-relative data/content)

"hostile perceived" = the inline loop in TacticalDecisionSystem.evaluate_entity_intent found at least one neighbour that
passed the perception gate AND is_hostile_compat (observed by wrapping is_hostile_compat and reading the caller frame's
locals, so the definition is the code's own). "in reach" = such a hostile at Manhattan distance <= entity.combat.range.
"past early" = the decision got past the panic and leash returns (EntityIdentityResolver.resolve(entity) was reached)."""
import collections
import json
import os
import sys

ROOT = sys.argv[1]
TICKS = int(sys.argv[2]) if len(sys.argv) > 2 else 70
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 42
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import src  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
from src.content_semantics.faction import get_faction_semantics_service  # noqa: E402
from src.domains.campaigns.orchestrator import CampaignOrchestrator  # noqa: E402
from src.engine.scenario_runtime import ScenarioRuntimeService  # noqa: E402
from src.engine.tactical import TacticalDecisionSystem  # noqa: E402
from src.entities.identity_resolver import EntityIdentityResolver  # noqa: E402
from tests.integration.campaigns.test_catalog_entity_spawn_wiring import _campaign_life_arc_shaped_manifest  # noqa: E402

CUR = None
ROWS = []
ENT_DECISIONS = collections.Counter()

svc_cls = type(get_faction_semantics_service())
_hc = svc_cls.is_hostile_compat


def hc(self, *a, **k):
    res = _hc(self, *a, **k)
    f = sys._getframe(1)
    if CUR is not None and f.f_code.co_name == "evaluate_entity_intent":
        n, ent = f.f_locals.get("n"), f.f_locals.get("entity")
        if res and n is not None and ent is not None:
            CUR["hostiles"].add(n.id)
            d = abs(ent.navigation.position[0] - n.navigation.position[0]) + abs(ent.navigation.position[1] - n.navigation.position[1])
            if d <= ent.combat.range:
                CUR["in_reach"].add(n.id)
    return res


svc_cls.is_hostile_compat = hc

_rs = EntityIdentityResolver.resolve


def rs(self, e, *a, **k):
    f = sys._getframe(1)
    if CUR is not None and f.f_code.co_name == "evaluate_entity_intent" and f.f_locals.get("entity") is e:
        CUR["past_early"] = True
    return _rs(self, e, *a, **k)


EntityIdentityResolver.resolve = rs

_ev = TacticalDecisionSystem.evaluate_entity_intent


def ev(state, entity, *a, **k):
    global CUR
    CUR = {"hostiles": set(), "in_reach": set(), "past_early": False}
    try:
        out = _ev(state, entity, *a, **k)
    finally:
        cur, CUR = CUR, None
    task = getattr(out, "task", None)
    if task is None:
        choice = "no task change"
    else:
        pl = task.payload_set or {}
        choice = "%s:%s" % (task.work_kind_set, pl.get("action") or pl.get("reason") or ("pursue" if pl.get("target_id") is not None else "-"))
    hp = entity.combat.hp / max(1, entity.combat.max_hp)
    ROWS.append({"entity": entity.id, "tick": state.tick, "hostile": bool(cur["hostiles"]), "in_reach": bool(cur["in_reach"]),
                 "past_early": cur["past_early"], "choice": choice, "hp": round(hp, 2)})
    ENT_DECISIONS[entity.id] += 1
    return out


TacticalDecisionSystem.evaluate_entity_intent = staticmethod(ev)

orch = CampaignOrchestrator(_campaign_life_arc_shaped_manifest(tick_limit=TICKS))
spec = orch._manifest.episodes[0]
svc = ScenarioRuntimeService(spec, initial_state=orch._build_initial_state(SEED, spec), scenario_event_recorder=None)
svc._kernel = svc._build_kernel()
svc.start(tick_limit=TICKS)
svc.abort()

n = len(ROWS)
print("CONFIG ticks=%d seed=%d" % (TICKS, SEED))
print("DECISIONS", n, "entities deciding", len(ENT_DECISIONS), "per-entity max/median", max(ENT_DECISIONS.values()),
      sorted(ENT_DECISIONS.values())[len(ENT_DECISIONS) // 2])
print("HOSTILE-PERCEIVED", sum(r["hostile"] for r in ROWS), "| IN-REACH", sum(r["in_reach"] for r in ROWS),
      "| PAST-EARLY-RETURNS", sum(r["past_early"] for r in ROWS))
groups = collections.defaultdict(collections.Counter)
for r in ROWS:
    key = ("hostile+in_reach" if r["in_reach"] else "hostile (not in reach)") if r["hostile"] else (
        "no hostile, past panic/leash" if r["past_early"] else "returned before the hostile scan")
    groups[key][r["choice"]] += 1
for k in ("hostile+in_reach", "hostile (not in reach)", "no hostile, past panic/leash", "returned before the hostile scan"):
    print("GROUP", k, sum(groups[k].values()), json.dumps(dict(groups[k].most_common())))
att = [r for r in ROWS if any(w in r["choice"] for w in ("ATTACK", "SKILL", "AOE"))]
print("ATTACK-DECISIONS", len(att), json.dumps(collections.Counter(r["choice"] for r in att)))
hrows = [r for r in ROWS if r["hostile"]]
print("HOSTILE-DECISION hp: ", json.dumps(sorted(r["hp"] for r in hrows)))

for r in ROWS:
    if r["in_reach"] or any(w in r["choice"] for w in ("ATTACK", "SKILL", "AOE")):
        print("IN-REACH-ROWS", json.dumps(r))
