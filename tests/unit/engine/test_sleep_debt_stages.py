"""Decision 41 (SURV-02): sleep debt weakens, then collapses the subject where it stands, and never costs health.

Stage order and relations only; the lines are the table's own (80 weakened, 98 collapse, 60 wake) and are read from it, never retyped here.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

import src.core.registries  # noqa: F401
from src.core.builder import V2EntityBuilder
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, TaskComponent
from src.core.updates import BiologicalUpdate, EntityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.pipeline_phases.actions import _survival_action_ends
from src.engine.sleep_debt import (
    COLLAPSE_FLAG,
    SLEEP_DEBT,
    collapse_update,
    is_rested_enough,
    is_weakened,
    must_collapse,
    recovery_scale,
    sleep_done,
)
from src.engine.tactical import TacticalDecisionSystem


def _subject(debt, hp=100, hunger=0.0, readiness=100.0, eid=1):
    return (V2EntityBuilder(eid).kind("HERO").location(10.0, 10.0).biological(hunger=hunger, sleep_debt=debt)
            .combat(hp=hp, max_hp=hp, readiness=readiness).lifecycle(active=True, age_ticks=0, max_age_ticks=100_000).build())


def test_the_stages_follow_the_table_in_order():
    t = SLEEP_DEBT
    assert t.weakened_line < t.collapse_line and t.wake_line < t.weakened_line
    assert not is_weakened(t.weakened_line) and is_weakened(t.weakened_line + 0.1)  # the pre-existing "above 80" EXHAUSTION line
    assert not must_collapse(t.collapse_line - 0.1) and must_collapse(t.collapse_line)
    assert is_rested_enough(t.wake_line - 0.1) and not is_rested_enough(t.wake_line)


def test_a_subject_past_the_collapse_line_loses_no_health_however_long_it_stays_there():
    state = AuthoritativeState(tick=0, seed=1, entities={1: _subject(SLEEP_DEBT.collapse_line + 1.5)})
    for _ in range(300):
        state = ApplyPath.apply_generation(state, StateUpdate())
    survivor = state.entities[1]
    assert survivor.combat.hp == 100 and survivor.combat.alive and survivor.lifecycle.passive_death_cause is None


def test_a_weakened_body_recovers_more_slowly_and_the_worse_of_hunger_and_sleep_decides():
    def regen(**bio):
        state = AuthoritativeState(tick=0, seed=1, entities={1: _subject(bio.get("debt", 0.0), hunger=bio.get("hunger", 0.0), readiness=0.0)})
        return ApplyPath.apply_generation(state, StateUpdate()).entities[1].combat.readiness

    rested, tired, hungry, both = regen(), regen(debt=SLEEP_DEBT.weakened_line + 5), regen(hunger=90.0), regen(debt=SLEEP_DEBT.weakened_line + 5, hunger=90.0)
    assert tired < rested and tired == hungry and both == tired  # the worse stage, not a compounding of the two
    assert recovery_scale(0.0) == 1.0 and recovery_scale(SLEEP_DEBT.weakened_line + 5) < 1.0


def test_the_decision_of_a_subject_at_the_collapse_line_is_a_held_sleep_where_it_stands_and_not_before():
    state = AuthoritativeState(tick=1, seed=1, entities={1: _subject(SLEEP_DEBT.collapse_line)})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, state.entities[1], neighbors=[])
    assert update.task.payload_set == {"action": "SLEEP", COLLAPSE_FLAG: True} and update.task.work_kind_set == "ENTITY_ACT"
    assert update.navigation.target_clear and update.navigation.movement_mode_set == MovementMode.HOLD
    rested = AuthoritativeState(tick=1, seed=1, entities={1: _subject(SLEEP_DEBT.collapse_line - 1)})
    other = TacticalDecisionSystem.evaluate_entity_intent(rested, rested.entities[1], neighbors=[])
    assert not (other.task and (other.task.payload_set or {}).get(COLLAPSE_FLAG))
    assert collapse_update(state.entities[1]).task.payload_set[COLLAPSE_FLAG] is True


def _walking(debt):
    e = _subject(debt)
    return replace(e, task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (40.0, 40.0), "reason": "WANDER"}))


def test_a_held_walk_stops_where_it_stands_when_the_debt_reaches_the_collapse_line():
    assert MovementCandidateSelector.move_ends_here(_walking(SLEEP_DEBT.collapse_line), {1: _walking(SLEEP_DEBT.collapse_line)}) is True
    assert MovementCandidateSelector.move_ends_here(_walking(SLEEP_DEBT.collapse_line - 1), {1: _walking(SLEEP_DEBT.collapse_line - 1)}) is False


def test_a_collapse_sleep_is_held_until_the_debt_is_below_the_wake_line_but_an_ordinary_sleep_ends_at_once():
    relief = EntityUpdate(entity_id=1, biological=BiologicalUpdate(sleep_debt_delta=-20.0))
    deep, nearly = _subject(SLEEP_DEBT.collapse_line), _subject(SLEEP_DEBT.wake_line + 10.0)
    held = {COLLAPSE_FLAG: True}
    assert _survival_action_ends("SLEEP", True, "SUCCESS", relief, (held, deep)) is False  # 98 - 20 is still above the wake line
    assert _survival_action_ends("SLEEP", True, "SUCCESS", relief, (held, nearly)) is True  # 70 - 20 is below it
    assert _survival_action_ends("SLEEP", True, "SUCCESS", relief, ({}, deep)) is True  # an ordinary SLEEP is one success
    assert _survival_action_ends("SLEEP", True, "FAILURE", relief, (held, nearly)) is False
    assert sleep_done(nearly, relief) and not sleep_done(deep, relief)
