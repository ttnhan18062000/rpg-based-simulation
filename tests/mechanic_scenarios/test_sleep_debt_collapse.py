"""LB-S19 (owner decision 41, SURV-02): a subject that has gone far too long without sleep is weaker first, then falls asleep where it stands, cannot
act while asleep, and wakes once enough of the debt is slept off. Its health never drops from lack of sleep. A rested one does none of this.

Staging: a compiled world reduced to one subject (no hostiles, no hazard) at full health, hunger low, part way along a committed walk across open ground,
so a collapse shows as a stop away from any bed. Everything is read from authoritative state, per tick, through the real kernel.
MAIN       debt just below the collapse line: weakened, then collapsed on the occupied tile, no action and no movement while collapsed, debt falling,
           then awake below the wake line and walking on; health never below its staged value.
CONTROL    debt low: never weakened, never collapses, completes its walk, health unchanged.
SECOND     the main arm repeated for a wolf: the rule is not people-only.
The lines and effect sizes are the table's (engineering, not observable); this checks the stage order, "no action while collapsed", waking and "no HP loss".
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.core.movement_modes import MovementMode
from src.core.state import TaskComponent
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.sleep_debt import SLEEP_DEBT, is_weakened
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("scenario")]

WORLD, SEED = "frontier_living_world", 42
WINDOW = 700
WALK_TO = (58.0, 30.0)


def _stage(species, debt):
    state = compile_world(WORLD, SEED)
    subject = next(e for e in state.entities.values() if (e.identity.properties or {}).get("species_id") == species and e.combat.alive)
    subject = replace(
        subject, biological=replace(subject.biological, hunger=0.0, sleep_debt=debt),
        navigation=replace(subject.navigation, position=(38.0, 30.0), target=WALK_TO, movement_mode=MovementMode.WANDER, home_position=None, leash_radius=0.0),
        task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": WALK_TO, "reason": "WANDER"}))
    return replace(state, entities={subject.id: subject}, buildings={}, building_tiles={}, resource_nodes={}, hazards={} if hasattr(state, "hazards") else None) \
        if hasattr(state, "hazards") else replace(state, entities={subject.id: subject}, buildings={}, building_tiles={}, resource_nodes={}), subject.id


def _run(species, debt, ticks=WINDOW):
    state, sid = _stage(species, debt)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    start_hp = state.entities[sid].combat.hp
    rows = []
    try:
        for _ in range(ticks):
            kernel.tick_once()
            e = kernel._state.entities[sid]
            rows.append({"tick": kernel._state.tick, "debt": e.biological.sleep_debt, "pos": e.navigation.position, "hp": e.combat.hp, "alive": e.combat.alive,
                         "asleep": e.task.payload.get("action") == "SLEEP" and bool(e.task.payload.get("collapse"))})
    finally:
        kernel.shutdown()
    return rows, start_hp


@pytest.mark.parametrize("species", ["human", "wolf"])
def test_main_weakened_then_collapsed_where_it_stands_then_awake_and_walking_with_its_health_intact(species):
    # just below the collapse line, above the weakened line, so the debt crosses the collapse line within the window
    rows, start_hp = _run(species, SLEEP_DEBT.collapse_line - 1.0)
    assert is_weakened(rows[0]["debt"]), "staged weakened"
    first = next(i for i, r in enumerate(rows) if r["asleep"])
    woke = next(i for i, r in enumerate(rows) if i > first and not r["asleep"])
    spot = rows[first]["pos"]
    assert all(r["pos"] == spot for r in rows[first:woke]), "collapsed on the tile it occupied, and does not move while asleep"
    assert rows[woke]["debt"] < SLEEP_DEBT.wake_line, "awake only once the debt is below the wake line"
    assert rows[woke]["debt"] < rows[first]["debt"] - 10.0, "the debt is slept off while it is asleep"
    assert woke - first >= 100, "a collapse is a deep sleep of hundreds of ticks, not a few"
    assert any(r["pos"] != spot for r in rows[woke:]), "and it walks on afterwards"
    assert all(r["hp"] >= start_hp and r["alive"] for r in rows), "health never lower than at staging"


def test_control_a_rested_subject_is_never_weakened_never_collapses_and_walks():
    rows, start_hp = _run("human", 5.0)
    assert not any(r["asleep"] for r in rows) and not any(is_weakened(r["debt"]) for r in rows)
    assert rows[-1]["pos"] != rows[0]["pos"] and all(r["hp"] == start_hp for r in rows)
