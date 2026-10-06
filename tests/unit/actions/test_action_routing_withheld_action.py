"""TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS:
an action the router dispatched but did nothing with (the combat-posture gate, an unrecognised
action) must be REPORTED as a typed failure, so ActionRoutingPhase.route() clears the task and
the brain re-decides -- instead of a bare no-op that annotates `outcome: SUCCESS`, keeps the task
and has the scheduler re-dispatch the same do-nothing action every tick (measured: ~851 ticks).

Must not change: a risk-ACCEPTED posture still dispatches, absence of a recorded posture (or one
recorded for a different target) still does not withhold, and a stale annotation `reason` does not
outlive the tick it described while a decision-time `reason` (no `outcome` beside it) is kept.
"""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.domain.action_router import ActionRouter
from src.engine.pipeline_phases.actions import ActionRoutingPhase

REJECTED_POSTURES = ["watch", "avoid", "panic_flee", "retreat"]
ACCEPTED_POSTURES = ["engage", "probe", "skirmish", "vengeance_engage"]


def _attacker(posture: str | None = None, posture_target: int | None = 2):
    props = {}
    if posture is not None:
        props = {"last_combat_posture": posture, "last_combat_posture_target": posture_target}
    return (
        V2EntityBuilder(1)
        .kind("monster")
        .location(10.0, 10.0)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0, attack_range=10)
        .lifecycle(active=True)
        .identity(faction=Faction.HERO_GUILD, properties=props)
        .build()
    )


def _target():
    return (
        V2EntityBuilder(2)
        .kind("monster")
        .location(10.0, 11.0)
        .combat(hp=100, max_hp=100, alive=True)
        .lifecycle(active=True)
        .identity(faction=Faction.MONSTER_HORDE)
        .build()
    )


def _route(attacker, payload: dict):
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: _target()})
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set=payload))
    })
    return ActionRoutingPhase.route(state, update)


@pytest.mark.parametrize("posture", REJECTED_POSTURES)
def test_posture_withheld_attack_clears_the_task_and_is_reported(posture):
    refined = _route(_attacker(posture), {"action": "ATTACK", "target_id": 2})

    assert refined.entity_updates[1].task.payload_set == {}
    assert refined.rejections_delta.get(ReasonCode.ACTION_WITHHELD_BY_POSTURE.value) == 1
    [event] = [e for e in refined.rejection_events if e.actor_id == 1]
    assert event.reason == ReasonCode.ACTION_WITHHELD_BY_POSTURE
    assert event.action_kind == "ATTACK"
    assert event.target_id == 2


def test_posture_withheld_skill_clears_the_task_too():
    """The gate covers ATTACK and SKILL; the clear is keyed to the reported reason, not to ATTACK."""
    refined = _route(_attacker("avoid"), {"action": "SKILL", "target_id": 2, "skill_id": "any"})

    assert refined.entity_updates[1].task.payload_set == {}
    assert refined.rejections_delta.get(ReasonCode.ACTION_WITHHELD_BY_POSTURE.value) == 1


@pytest.mark.parametrize("posture", ACCEPTED_POSTURES)
def test_risk_accepted_posture_still_dispatches(posture):
    refined = _route(_attacker(posture), {"action": "ATTACK", "target_id": 2})

    payload = refined.entity_updates[1].task.payload_set
    assert payload.get("target_id") == 2
    assert payload.get("outcome") == "SUCCESS"
    assert ReasonCode.ACTION_WITHHELD_BY_POSTURE.value not in refined.rejections_delta


def test_absent_posture_does_not_withhold():
    refined = _route(_attacker(None), {"action": "ATTACK", "target_id": 2})

    assert refined.entity_updates[1].task.payload_set.get("outcome") == "SUCCESS"
    assert ReasonCode.ACTION_WITHHELD_BY_POSTURE.value not in refined.rejections_delta


def test_posture_recorded_for_another_target_does_not_withhold():
    refined = _route(_attacker("avoid", posture_target=99), {"action": "ATTACK", "target_id": 2})

    assert refined.entity_updates[1].task.payload_set.get("outcome") == "SUCCESS"
    assert ReasonCode.ACTION_WITHHELD_BY_POSTURE.value not in refined.rejections_delta


def test_unsupported_action_clears_the_task_and_is_reported():
    refined = _route(_attacker(None), {"action": "NOT_A_REAL_ACTION", "target_id": 2})

    assert refined.entity_updates[1].task.payload_set == {}
    assert refined.rejections_delta.get(ReasonCode.UNSUPPORTED_ACTION.value) == 1


def test_router_reports_the_withheld_attack_without_spending_readiness():
    result = ActionRouter.execute_action(_attacker("avoid"), {"action": "ATTACK", "target_id": 2}, 1)

    upd = result[1]
    assert upd.navigation.failure_reason == ReasonCode.ACTION_WITHHELD_BY_POSTURE
    assert upd.readiness_delta == 0.0


def test_stale_annotation_reason_does_not_survive_into_a_later_success():
    """The payload carries last tick's annotation (outcome + reason); this tick's attack is legal."""
    refined = _route(
        _attacker(None),
        {"action": "ATTACK", "target_id": 2, "outcome": "FAILURE", "reason": "OUT_OF_RANGE"},
    )

    payload = refined.entity_updates[1].task.payload_set
    assert payload.get("outcome") == "SUCCESS"
    assert "reason" not in payload


def test_decision_time_reason_without_an_outcome_is_kept():
    refined = _route(_attacker(None), {"action": "ATTACK", "target_id": 2, "reason": "DECISION_DRIVER"})

    payload = refined.entity_updates[1].task.payload_set
    assert payload.get("outcome") == "SUCCESS"
    assert payload.get("reason") == "DECISION_DRIVER"


def test_dead_target_still_clears_through_the_existing_branch():
    dead = (
        V2EntityBuilder(2)
        .kind("monster")
        .location(10.0, 11.0)
        .combat(hp=100, max_hp=100, alive=False)
        .lifecycle(active=False)
        .identity(faction=Faction.MONSTER_HORDE)
        .build()
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: _attacker(None), 2: dead})
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2}))
    })

    refined = ActionRoutingPhase.route(state, update)

    assert refined.entity_updates[1].task.payload_set == {}
    assert refined.rejections_delta.get(ReasonCode.TARGET_INCAPACITATED.value) == 1
