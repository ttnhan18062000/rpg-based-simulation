"""Hunger wakes a sleeper (SURV-07 x decision 41; owner ruling 2026-10-11).

TCK-20261011-HUNGER-WAKES-A-SLEEPER: a held SLEEP or REST ran no brain, so a subject that fell asleep at hunger 96 slept through its own starvation
(traced: two merchants and a scout, 300 to 400 ticks, one with 81 gold). Hunger at ESCALATION_ONSET of its line now wakes the brain of a sleeper on the
need-wake cadence; a sleeper's debt is high by nature, so only hunger wakes it. Staging asserts the wake, its bounds and the decision it leads to.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, TaskComponent
from src.engine.cadence import SystemCadence
from src.engine.need_pull import ESCALATION_ONSET, HUNGER_LINE, hunger_is_pressing
from src.engine.policy import GovernorPolicy
from src.engine.scheduler import NEED_WAKE_CADENCE, DeterministicScheduler
from src.engine.sleep_debt import COLLAPSE_FLAG, COLLAPSE_LINE
from src.engine.tactical import TacticalDecisionSystem


def _sleeper(eid=1, hunger=0.0, debt=70.0, action="SLEEP", collapse=False):
    e = (V2EntityBuilder(eid).kind("hero").location(10.0, 10.0).combat(hp=100, max_hp=100, readiness=100.0, alive=True).lifecycle(active=True)
         .biological(hunger=hunger, sleep_debt=debt).build())
    payload = {"action": action, **({COLLAPSE_FLAG: True} if collapse else {})}
    return replace(e, task=TaskComponent(work_kind="ENTITY_ACT", payload=payload))


def _brain_ticks(entity, ticks):
    policy = GovernorPolicy(system_cadence=SystemCadence(strategic_intelligence=10))
    out = []
    for t in ticks:
        state = AuthoritativeState(tick=t, seed=1, entities={entity.id: entity})
        items, _ = DeterministicScheduler().select_work(state, policy)
        if any(i.owner_id == entity.id and i.work_kind == "ENTITY_BRAIN" for i in items):
            out.append(t)
    return out


def test_the_trigger_is_hunger_at_the_escalation_onset_with_no_new_constant():
    assert hunger_is_pressing(ESCALATION_ONSET * HUNGER_LINE) and not hunger_is_pressing(ESCALATION_ONSET * HUNGER_LINE - 1.0)


def test_a_chosen_sleep_or_rest_is_woken_once_per_cadence_while_hunger_is_pressing():
    for action in ("SLEEP", "REST"):
        ticks = _brain_ticks(_sleeper(hunger=80.0, action=action), range(1, 1 + 3 * NEED_WAKE_CADENCE))
        assert len(ticks) == 3 and all(b - a == NEED_WAKE_CADENCE for a, b in zip(ticks, ticks[1:]))


def test_a_sated_sleeper_is_not_woken_and_a_high_debt_alone_does_not_wake_it():
    assert _brain_ticks(_sleeper(hunger=10.0, debt=70.0), range(1, 1 + 3 * NEED_WAKE_CADENCE)) == []
    assert _brain_ticks(_sleeper(hunger=10.0, debt=95.0), range(1, 1 + 3 * NEED_WAKE_CADENCE)) == []   # a sleeper's debt is high by nature


def test_the_wake_is_staggered_by_entity_id():
    first = _brain_ticks(_sleeper(eid=1, hunger=90.0), range(1, 1 + NEED_WAKE_CADENCE))
    second = _brain_ticks(_sleeper(eid=2, hunger=90.0), range(1, 1 + NEED_WAKE_CADENCE))
    assert first and second and first != second


def test_a_collapse_is_woken_too_but_its_decision_is_the_collapse_again_until_the_debt_is_below_the_line():
    held = _sleeper(hunger=90.0, debt=COLLAPSE_LINE + 1.0, collapse=True)
    assert _brain_ticks(held, range(1, 1 + NEED_WAKE_CADENCE))             # the brain runs
    state = AuthoritativeState(tick=1, seed=1, entities={1: held})
    at_line = TacticalDecisionSystem.evaluate_entity_intent(state, held)
    assert at_line.task.payload_set["action"] == "SLEEP" and at_line.task.payload_set[COLLAPSE_FLAG]   # the hold stays: no hunger decision yet


def test_below_the_collapse_line_the_decision_is_free_so_hunger_can_end_the_sleep():
    weak = _sleeper(hunger=90.0, debt=COLLAPSE_LINE - 1.0, collapse=True)
    state = AuthoritativeState(tick=1, seed=1, entities={1: weak})
    free = TacticalDecisionSystem.evaluate_entity_intent(state, weak)
    assert free.task is None or not (free.task.payload_set or {}).get(COLLAPSE_FLAG)   # no collapse re-issued: the strategic layer may decide to eat


def test_no_wake_collapse_loop_the_brain_runs_once_per_cadence_not_every_tick():
    held = _sleeper(hunger=95.0, debt=COLLAPSE_LINE + 1.0, collapse=True)
    ticks = _brain_ticks(held, range(1, 101))
    assert len(ticks) == 100 // NEED_WAKE_CADENCE and all(b - a == NEED_WAKE_CADENCE for a, b in zip(ticks, ticks[1:]))
