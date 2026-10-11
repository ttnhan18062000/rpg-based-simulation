"""A pressing biological need wakes the brain of an entity holding a move (SURV-07, decision 32 applied to hunger and sleep).

TCK-20261009-HEROES-ON-A-LEASH-NEVER-SEEK-FOOD-AND-STARVE-WITHOUT-ONE-EAT-ATTEMPT: a held move runs no brain, so a move that
cannot complete (a destination occupied by another, a retreat whose threat is gone) held its owner until it starved, though the
hunger goal already ranked first. Staging asserts the wake and its bounds, never a death count.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, TaskComponent
from src.engine.cadence import SystemCadence
from src.engine.need_pull import ESCALATION_ONSET, HUNGER_LINE, SLEEP_LINE, need_is_pressing
from src.engine.policy import GovernorPolicy
from src.engine.scheduler import NEED_WAKE_CADENCE, DeterministicScheduler
from src.engine.tactical import TacticalDecisionSystem
from tests.unit.combat.test_tactical_destinations import _entity, _state


def _holder(eid=1, hunger=0.0, sleep_debt=0.0, work_kind="ENTITY_MOVE", reason="REGROUP"):
    e = (V2EntityBuilder(eid).kind("hero").location(10.0, 10.0)
         .combat(hp=100, max_hp=100, readiness=100.0, alive=True).lifecycle(active=True)
         .biological(hunger=hunger, sleep_debt=sleep_debt).build())
    payload = {"target_position": (30.0, 30.0), "reason": reason} if work_kind == "ENTITY_MOVE" else {"action": "ATTACK", "target_id": 9}
    return replace(e, task=TaskComponent(work_kind=work_kind, payload=payload))


def _brain_ticks(entity, ticks):
    policy = GovernorPolicy(system_cadence=SystemCadence(strategic_intelligence=10))
    out = []
    for t in ticks:
        state = AuthoritativeState(tick=t, seed=1, entities={entity.id: entity})
        items, _ = DeterministicScheduler().select_work(state, policy)
        if any(i.owner_id == entity.id and i.work_kind == "ENTITY_BRAIN" for i in items):
            out.append(t)
    return out


def test_the_pressing_point_is_the_escalation_onset_of_each_consequence_line():
    assert need_is_pressing(ESCALATION_ONSET * HUNGER_LINE, 0.0)
    assert not need_is_pressing(ESCALATION_ONSET * HUNGER_LINE - 1.0, 0.0)
    assert need_is_pressing(0.0, ESCALATION_ONSET * SLEEP_LINE)
    assert not need_is_pressing(0.0, ESCALATION_ONSET * SLEEP_LINE - 1.0)


def test_a_held_move_is_woken_once_per_cadence_while_hunger_is_pressing():
    ticks = _brain_ticks(_holder(hunger=80.0), range(1, 1 + 3 * NEED_WAKE_CADENCE))
    assert len(ticks) == 3 and all(b - a == NEED_WAKE_CADENCE for a, b in zip(ticks, ticks[1:]))


def test_sleep_debt_wakes_a_held_move_the_same_way():
    assert len(_brain_ticks(_holder(sleep_debt=90.0), range(1, 1 + 2 * NEED_WAKE_CADENCE))) == 2


def test_no_wake_below_the_onset_and_none_for_an_action_holder():
    assert _brain_ticks(_holder(hunger=10.0, sleep_debt=10.0), range(1, 1 + 3 * NEED_WAKE_CADENCE)) == []
    assert _brain_ticks(_holder(hunger=90.0, work_kind="ENTITY_ACT"), range(1, 1 + 3 * NEED_WAKE_CADENCE)) == []


def test_a_held_flight_is_woken_too_because_waking_is_only_a_re_decision():
    # A present threat is seen again by the decision and re-issues the flight; a flight whose threat is gone is released.
    assert _brain_ticks(_holder(hunger=90.0, reason="PANIC_RETREAT"), range(1, 1 + NEED_WAKE_CADENCE))


def test_the_wake_is_staggered_by_entity_id():
    first = _brain_ticks(_holder(eid=1, hunger=90.0), range(1, 1 + NEED_WAKE_CADENCE))
    second = _brain_ticks(_holder(eid=2, hunger=90.0), range(1, 1 + NEED_WAKE_CADENCE))
    assert first and second and first != second


def test_a_woken_flight_stays_a_flight_while_the_threat_is_present_and_is_released_when_it_is_gone():
    # Waking is only a re-decision (SURV-07: a present threat to life is the one thing that outranks a pressing need).
    me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(20.0, 20.0))
    foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 21.0))
    present = TacticalDecisionSystem.evaluate_entity_intent(_state(me, foe), me)
    assert present.task.payload_set["reason"] == "PANIC_RETREAT"  # the threat is still there: the flight is re-issued

    healthy = _entity(1, Faction.HERO_GUILD, hp=100, pos=(20.0, 20.0))
    held = replace(healthy, task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (30.0, 30.0), "reason": "PANIC_RETREAT"}))
    gone = TacticalDecisionSystem.evaluate_entity_intent(_state(held), held)
    assert gone.task is None or (gone.task.payload_set or {}).get("reason") != "PANIC_RETREAT"  # no threat: the decision is free
