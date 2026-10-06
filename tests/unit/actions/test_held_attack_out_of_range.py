"""TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED: an ATTACK that comes back
OUT_OF_RANGE ends its task, so the scheduler re-runs the brain (an idle ENTITY_ACT has an empty payload,
scheduler.py `is_idle_act`) instead of re-dispatching the same swing every few ticks while the pair stays put
(measured: one diagonal melee pair held 267 swings in a 2000-tick run). Melee adjacency is orthogonal
(Manhattan <= 1, world rule MOV-07).

Must not change: an in-reach attack keeps its task (the existing sticky-attack behaviour), a readiness failure keeps
its task (readiness regens and the same swing can land), and a ranged attacker inside its range is not cleared.
"""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.pipeline_phases.actions import ActionRoutingPhase, _is_unrecoverable_action_failure

PAYLOAD = {"action": "ATTACK", "target_id": 2}


def _fighter(eid, pos, faction, *, attack_range=1, readiness=100.0):
    return (
        V2EntityBuilder(eid)
        .kind("monster")
        .location(*pos)
        .combat(hp=100, max_hp=100, alive=True, readiness=readiness, attack_range=attack_range)
        .lifecycle(active=True)
        .identity(faction=faction)
        .build()
    )


def _route(target_pos, *, attack_range=1, readiness=100.0):
    attacker = _fighter(1, (10.0, 10.0), Faction.HERO_GUILD, attack_range=attack_range, readiness=readiness)
    target = _fighter(2, target_pos, Faction.MONSTER_HORDE)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set=dict(PAYLOAD)))
    })
    return ActionRoutingPhase.route(state, update)


@pytest.mark.parametrize("target_pos", [(11.0, 11.0), (9.0, 9.0), (10.0, 15.0)], ids=["diagonal", "other-diagonal", "far"])
def test_out_of_range_melee_attack_ends_the_task_and_is_reported(target_pos):
    refined = _route(target_pos)

    assert refined.entity_updates[1].task.payload_set == {}  # idle ENTITY_ACT: the scheduler re-runs the brain
    assert refined.rejections_delta.get(ReasonCode.OUT_OF_RANGE.value) == 1
    [event] = [e for e in refined.rejection_events if e.actor_id == 1]
    assert event.reason == ReasonCode.OUT_OF_RANGE
    assert event.target_id == 2


def test_orthogonally_adjacent_attack_still_lands_and_keeps_its_task():
    refined = _route((10.0, 11.0))

    payload = refined.entity_updates[1].task.payload_set
    assert payload.get("target_id") == 2 and payload.get("outcome") == "SUCCESS"
    assert ReasonCode.OUT_OF_RANGE.value not in refined.rejections_delta


def test_ranged_attacker_inside_its_range_is_not_cleared():
    refined = _route((10.0, 14.0), attack_range=5)

    assert refined.entity_updates[1].task.payload_set.get("outcome") == "SUCCESS"
    assert ReasonCode.OUT_OF_RANGE.value not in refined.rejections_delta


def test_ranged_attacker_beyond_its_range_is_cleared():
    refined = _route((10.0, 30.0), attack_range=5)

    assert refined.entity_updates[1].task.payload_set == {}
    assert refined.rejections_delta.get(ReasonCode.OUT_OF_RANGE.value) == 1


def test_readiness_failure_keeps_the_task():
    """INSUFFICIENT_READINESS is recoverable (readiness regens), unlike out of range: unchanged."""
    refined = _route((10.0, 11.0), readiness=40.0)

    payload = refined.entity_updates[1].task.payload_set
    assert payload.get("target_id") == 2 and payload.get("outcome") == "FAILURE"
    assert payload.get("reason") == ReasonCode.INSUFFICIENT_READINESS.value


class TestFailureClassification:
    def test_out_of_range_ends_only_an_attack(self):
        reason = ReasonCode.OUT_OF_RANGE.value
        assert _is_unrecoverable_action_failure("ATTACK", "FAILURE", reason) is True
        assert _is_unrecoverable_action_failure("SKILL", "FAILURE", reason) is False
        assert _is_unrecoverable_action_failure("ATTACK", "SUCCESS", reason) is False

    def test_the_existing_dead_target_and_readiness_classification_is_unchanged(self):
        assert _is_unrecoverable_action_failure("ATTACK", "FAILURE", ReasonCode.TARGET_INCAPACITATED.value) is True
        assert _is_unrecoverable_action_failure("ATTACK", "FAILURE", ReasonCode.INSUFFICIENT_READINESS.value) is False
