"""LB-S19 second half (owner decision 41 and the designer's addition): the sleep pull aims at the nearest OPEN way, not always the inn.

Resting where the subject stands is always open (distance 0, except while a present threat outranks it); a bed is a way only within reach.
Two arms of one staging that differ only in how far the inn is: NEAR (inside the reach bound) the tired subject walks to it; FAR (outside) it
does not start a long walk but rests where it stands, and its debt falls. Read from authoritative state, per tick, through the real kernel.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.sleep_debt import SLEEP_DEBT
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("scenario")]

WORLD, SEED, WINDOW = "frontier_living_world", 42, 120
TIRED = 75.0  # above the point where the SURV-07 pull outranks ordinary goals, below the collapse line


def _stage(gap):
    state = compile_world(WORLD, SEED)
    inn = next(b for b in state.buildings.values() if b.kind == "inn")
    subject = next(e for e in state.entities.values() if (e.identity.properties or {}).get("species_id") == "human" and e.combat.alive)
    x, y = inn.position
    subject = replace(subject, biological=replace(subject.biological, hunger=0.0, sleep_debt=TIRED),
                      navigation=replace(subject.navigation, position=(x - float(gap), y), target=None, home_position=None, leash_radius=0.0))
    return replace(state, entities={subject.id: subject}, resource_nodes={}), subject.id, inn.position


def _run(gap):
    state, sid, inn_pos = _stage(gap)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    rows = []
    try:
        for _ in range(WINDOW):
            kernel.tick_once()
            e = kernel._state.entities[sid]
            rows.append({"debt": e.biological.sleep_debt, "dist": abs(e.navigation.position[0] - inn_pos[0]) + abs(e.navigation.position[1] - inn_pos[1]),
                         "rest": e.task.payload.get("action") in ("REST", "SLEEP")})
    finally:
        kernel.shutdown()
    return rows


def test_near_a_tired_subject_walks_to_a_bed_within_reach():
    rows = _run(SLEEP_DEBT.bed_reach / 2)
    assert min(r["dist"] for r in rows) < rows[0]["dist"] - 5.0, "it heads for the inn"
    assert rows[-1]["debt"] < TIRED, "and sleeps it off"


def test_far_the_sleep_goal_names_no_bed_beyond_reach_so_the_subject_rests_where_it_stands():
    """The goal itself (the scorer), not the walk: another goal (TownScorer's return to town, which also grows with sleep debt) can still walk a
    far subject home, and that is a different pull. Here the sleep goal has no target when the inn is beyond reach or outside the subject's range."""
    from src.ai.goals.scorers import SleepScorer

    near_state, sid, _ = _stage(SLEEP_DEBT.bed_reach / 2)
    far_state, fid, _ = _stage(SLEEP_DEBT.bed_reach * 3)
    assert SleepScorer().score(near_state.entities[sid], near_state).target_pos is not None
    assert SleepScorer().score(far_state.entities[fid], far_state).target_pos is None, "no bed beyond reach: rest where it stands"
    leashed = near_state.entities[sid]
    home = (leashed.navigation.position[0] - 100.0, leashed.navigation.position[1])
    leashed = replace(leashed, navigation=replace(leashed.navigation, home_position=home, leash_radius=5.0))
    assert SleepScorer().score(leashed, near_state).target_pos is None, "a bed outside a leashed subject's range is not a way"
    assert SleepScorer().score(leashed, near_state).utility > 0.0, "and the need still pulls (to rest in place)"
