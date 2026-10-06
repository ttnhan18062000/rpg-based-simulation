"""Measure OUT_OF_RANGE rejections inside execute_attack and how long a sticky repeat lasts.

usage: oor_probe.py <root> <world> <ticks>

Runs audit_mode=True with the tick budget disabled (the measurement standard), wraps
CombatActions.execute_attack, and records the legality verdict each call saw. A "repeat" is an
OUT_OF_RANGE verdict for the same (attacker, target) pair as that attacker's previous execute_attack
verdict was also OUT_OF_RANGE for. A "streak" is a maximal run of such verdicts for one pair;
its length is reported in verdicts and in ticks (first..last).
"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.engine.domain.combat_actions import CombatActions  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.legality import LegalityServiceV2  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)

C = collections.Counter()
LAST_VERDICT = []
PREV = {}  # attacker -> (target, reason, tick)
STREAK = {}  # (attacker, target) -> [first_tick, last_tick, n]
STREAKS = []

_vl = LegalityServiceV2.verify_attack_legality


def vl(attacker, target, state, *a, **k):
    res = _vl(attacker, target, state, *a, **k)
    LAST_VERDICT.append((attacker.id, target.id, state.tick, str(res[1]), attacker.combat.readiness))
    return res


LegalityServiceV2.verify_attack_legality = staticmethod(vl)
_ea = CombatActions.execute_attack


def ea(*a, **k):
    LAST_VERDICT.clear()
    r = _ea(*a, **k)
    C["execute_attack_calls"] += 1
    if not LAST_VERDICT:
        return r
    att, tgt, tick, reason, ready = LAST_VERDICT[-1]
    C[f"verdict.{reason}"] += 1
    key = (att, tgt)
    prev = PREV.get(att)
    oor = reason.endswith("OUT_OF_RANGE")
    if oor:
        C["oor_total"] += 1
        if prev and prev[0] == tgt and prev[1].endswith("OUT_OF_RANGE"):
            C["oor_repeat"] += 1
            s = STREAK[key]
            s[1], s[2] = tick, s[2] + 1
        else:
            STREAK[key] = [tick, tick, 1]
    else:
        if prev and prev[1].endswith("OUT_OF_RANGE"):
            STREAKS.append((prev[0], STREAK.pop((att, prev[0]), None)))
    PREV[att] = (tgt, reason, tick)
    return r


CombatActions.execute_attack = staticmethod(ea)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        k.tick_once()
finally:
    k.shutdown()
for key, s in STREAK.items():
    STREAKS.append((key[1], s))
lens = sorted(s[2] for _, s in STREAKS if s)
spans = sorted(s[1] - s[0] + 1 for _, s in STREAKS if s)
out = dict(sorted(C.items()))
out["streaks"] = len(lens)
out["streak_max_verdicts"] = lens[-1] if lens else 0
out["streak_max_ticks"] = spans[-1] if spans else 0
out["streaks_len_ge_2"] = sum(1 for n in lens if n >= 2)
print("OOR-PROBE", WORLD, TICKS, json.dumps(out))
