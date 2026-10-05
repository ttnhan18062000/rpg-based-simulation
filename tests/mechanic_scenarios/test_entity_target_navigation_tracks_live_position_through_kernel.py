"""A combat objective's navigation target tracks the target entity's LIVE position, through the real kernel
(TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES, AC1).

This is a regression guard, not a fix: on the current tree a combat objective is `defeat_enemy`, engagement is
the hostile branch, and the property already holds. Nothing else prevents it from regressing back to the
"point frozen at goal-win time" shape the ticket was filed for, and a unit test of the resolver cannot see
that, because the live path never calls the resolver for a combat objective.

World: ``mechanic_scenario_combat_judgement_withdrawal`` -- two catalog-hostile entities, both of whom move,
so the target moves after the objective is created.

Deliberately NOT asserted: that either entity attacks. Measured on this world, 120 ticks: both stay alive
at unchanged HP and oscillate; their navigation targets stay within one tile of the opponent's live position
at every sample, which is consistent with the documented single-axis diagonal pursuit limit
(docs/engine/known_limitations.md section 1.1), not with a frozen target point. Not investigated further here.
"""
import os

from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
SEED = 42
TICKS = 60
# Navigation steps one axis at a time, so a live target is allowed to lag the opponent by one step.
MAX_LAG = 2


def _run():
    repo = WorldRepository(os.path.join("data", "worlds"))
    spec, context = repo.load_world_with_context(WORLD_ID)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True, "no_replay": True}, executor=LocalSequentialExecutor())
    samples = []  # (tick, entity id, nav target, opponent position)
    targets_seen = {1: set(), 2: set()}
    try:
        for tick in range(TICKS):
            kernel.tick_once()
            entities = kernel._state.entities
            for eid, other in ((1, 2), (2, 1)):
                me, foe = entities[eid], entities[other]
                if me.navigation.target is None or not (me.combat.alive and foe.combat.alive):
                    continue
                targets_seen[eid].add(me.navigation.target)
                samples.append((tick, eid, me.navigation.target, foe.navigation.position))
    finally:
        kernel.shutdown()
    return samples, targets_seen


def test_navigation_target_tracks_the_opponents_live_position():
    samples, targets_seen = _run()

    assert samples, "both entities must pursue (non-vacuous): no navigation target was ever set"
    for tick, eid, target, foe_pos in samples:
        lag = abs(target[0] - foe_pos[0]) + abs(target[1] - foe_pos[1])
        assert lag <= MAX_LAG, f"tick {tick}: entity {eid} navigates to {target}, {lag} tiles from the live target {foe_pos}"


def test_navigation_target_is_not_frozen_while_the_opponent_moves():
    _, targets_seen = _run()

    assert all(targets_seen[eid] for eid in (1, 2))
    assert any(len(seen) >= 2 for seen in targets_seen.values()), "targets never changed: a frozen point"


def test_scenario_is_deterministic():
    assert _run() == _run()
