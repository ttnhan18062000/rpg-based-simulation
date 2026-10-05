"""Decision-path vs incidental (opportunity) combat, plus mutual tile swapping. usage: combat_volume.py <root> <world> <ticks>
Counters: execute_attack calls (decision path dispatch), resolve_attack calls split by is_opportunity_attack, and
'swap ticks' = ticks where two entities exchanged tiles (A moved to B's previous tile and B to A's)."""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
from src.config.profiles import PROD_SMALL
from src.engine.combat import CombatResolutionSystem
from src.engine.domain.combat_actions import CombatActions
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

C = collections.Counter()
_ea = CombatActions.execute_attack


def ea(*a, **k):
    C["decision_path.execute_attack_calls"] += 1
    return _ea(*a, **k)


CombatActions.execute_attack = staticmethod(ea)
_ra = CombatResolutionSystem.resolve_attack


def ra(attacker, defender, state, is_opportunity_attack=False, is_lethal=True):
    C["resolve_attack." + ("opportunity" if is_opportunity_attack else "non_opportunity")] += 1
    return _ra(attacker, defender, state, is_opportunity_attack, is_lethal)


CombatResolutionSystem.resolve_attack = staticmethod(ra)
_rm = CombatResolutionSystem.resolve_multi_attack


def rm(attackers, defender, state, is_opportunity_attack=False, is_lethal=True, *a, **k):
    C["resolve_multi_attack." + ("opportunity" if is_opportunity_attack else "other") + ".calls"] += 1
    C["resolve_multi_attack." + ("opportunity" if is_opportunity_attack else "other") + ".attackers"] += len(attackers)
    return _rm(attackers, defender, state, is_opportunity_attack, is_lethal, *a, **k)


CombatResolutionSystem.resolve_multi_attack = staticmethod(rm)
spec, ctx = WorldRepository(f"{ROOT}/data/worlds").load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
prev = {e.id: e.navigation.position for e in state.entities.values()}
try:
    for _ in range(TICKS):
        k.tick_once()
        cur = {e.id: e.navigation.position for e in k._state.entities.values() if e.combat.alive}
        moved = {i: (prev[i], cur[i]) for i in cur if i in prev and prev[i] != cur[i]}
        swapped = set()
        for i, (a0, a1) in moved.items():
            for j, (b0, b1) in moved.items():
                if i < j and a1 == b0 and b1 == a0:
                    swapped.add((i, j))
        C["swap_pairs_ticks"] += len(swapped)
        prev = {i: cur[i] for i in cur}
finally:
    k.shutdown()
print("COMBAT-VOLUME", WORLD, TICKS, json.dumps(dict(sorted(C.items()))))
