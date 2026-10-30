"""Set iteration order must not decide simulation outcomes (TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED).

Each case runs in subprocesses at several PYTHONHASHSEED values and compares the result, because the order of a
set of str follows the process hash seed and cannot be varied inside one process.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap

import pytest

SEEDS = ("0", "1", "2", "3", "4")


def _run(code: str, seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": seed}
    out = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], env=env, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _across_seeds(code: str) -> dict[str, str]:
    return {seed: _run(code, seed) for seed in SEEDS}


_SKILL_PICK = """
from src.core.skills import SKILL_REGISTRY
from src.engine.tactical import pick_highest_power_skill
skills = [SKILL_REGISTRY[i] for i in frozenset(["HEAVY_STRIKE", "fireball"])]
print(pick_highest_power_skill(skills).id)
"""


def test_equal_power_skills_pick_the_lowest_skill_id_at_every_seed():
    picks = _across_seeds(_SKILL_PICK)
    assert set(picks.values()) == {"HEAVY_STRIKE"}, picks


def test_positive_control_the_unkeyed_sort_flips_with_the_seed():
    """The old shape (sort on power alone, stable over set order) picks differently across seeds."""
    code = """
from src.core.skills import SKILL_REGISTRY
skills = [SKILL_REGISTRY[i] for i in frozenset(["HEAVY_STRIKE", "fireball"])]
skills.sort(key=lambda s: s.power, reverse=True)
print(skills[0].id)
"""
    assert len(set(_across_seeds(code).values())) > 1, "no seed in SEEDS flips the old shape, so the control proves nothing"


def test_higher_power_still_wins_over_a_lower_id():
    from src.core.skills import SKILL_REGISTRY
    from src.engine.tactical import pick_highest_power_skill

    weaker = SKILL_REGISTRY["swift_reflexes"]
    stronger = SKILL_REGISTRY["fireball"]
    assert stronger.power > weaker.power
    assert pick_highest_power_skill([weaker, stronger]) is stronger


_CONCERN_MERGE = """
import json
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import ConcernKind, ConcernState
from src.core.updates import StateUpdate
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
from src.systems.world_systems.routine import RoutineService

actor_id = 42
actor = V2EntityBuilder(actor_id).kind("hero").location(0.0, 0.0).build()
state = AuthoritativeState(seed=123, tick=(10 - (actor_id % 10)) % 10, entities={actor_id: actor})
concerns = [ConcernState(id=f"c{i:02d}", kind=ConcernKind.DANGER, urgency=0.5, created_tick=0) for i in range(12)]
RoutineService.evaluate_biological_needs = staticmethod(lambda *a, **k: list(concerns))
update = StrategicIntelligenceSystem.evaluate_all_concerns(state, StateUpdate())
print(json.dumps([c.id for c in update.entity_updates[actor_id].strategic.concerns_add_or_update]))
"""


def test_equal_urgency_concern_merge_is_ordered_by_id_at_every_seed():
    orders = _across_seeds(_CONCERN_MERGE)
    assert len(set(orders.values())) == 1, orders
    merged = json.loads(orders["0"])
    assert merged == sorted(merged) and len(merged) >= 12


def test_positive_control_the_set_merge_order_of_equal_urgency_concerns_flips_with_the_seed():
    code = """
import json
from src.core.strategic import ConcernKind, ConcernState
cs = [ConcernState(id=f"c{i:02d}", kind=ConcernKind.DANGER, urgency=0.5, created_tick=0) for i in range(12)]
print(json.dumps([c.id for c in list(set(cs))]))
"""
    assert len(set(_across_seeds(code).values())) > 1, "no seed flips the old set-order shape"


def test_update_merges_return_sorted_lists():
    from src.core.updates import IdentityUpdate

    a = IdentityUpdate(learned_skills=["z_skill", "b_skill"], traits_add=["t2"], traits_remove=["r2"])
    b = IdentityUpdate(learned_skills=["a_skill", "b_skill"], traits_add=["t1"], traits_remove=["r1"])
    merged = a.merge(b)
    assert merged.learned_skills == ["a_skill", "b_skill", "z_skill"]
    assert merged.traits_add == ["t1", "t2"]
    assert merged.traits_remove == ["r1", "r2"]
