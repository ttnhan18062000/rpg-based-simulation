"""A queued action rejected only for readiness is a wait, not a capability gap (CONFLICT-04 follow-up, divergence 2.88).

The rejection is still logged and the task is kept (the swing lands at readiness 100), but no ``blocker_nav_INSUFFICIENT_READINESS``
capability blocker is written: it was never resolved and made RESOLVE_BLOCKER score above zero.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.pipeline_phases.actions import ActionRoutingPhase


def _fighter(eid, pos, faction, readiness=100.0):
    return (V2EntityBuilder(eid).kind("monster").location(*pos)
            .combat(hp=100, max_hp=100, alive=True, readiness=readiness).lifecycle(active=True).identity(faction=faction).build())


def _route(readiness):
    state = AuthoritativeState(tick=1, seed=42, entities={
        1: _fighter(1, (10.0, 10.0), Faction.HERO_GUILD, readiness), 2: _fighter(2, (10.0, 11.0), Faction.MONSTER_HORDE)})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=TaskUpdate(
        work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "reason": "HOLD_BETWEEN_BLOWS", "target_id": 2}))})
    return ActionRoutingPhase.route(state, update)


def test_readiness_rejected_queued_attack_is_logged_keeps_its_task_and_writes_no_blocker():
    refined = _route(readiness=40.0)
    ent = refined.entity_updates[1]
    assert ent.task.payload_set["reason"] == ReasonCode.INSUFFICIENT_READINESS.value and ent.task.payload_set["outcome"] == "FAILURE"
    assert ent.task.payload_set["target_id"] == 2  # the task survives, so the swing lands at 100
    assert refined.rejections_delta.get(ReasonCode.INSUFFICIENT_READINESS.value) == 1
    assert ent.strategic is None  # nothing written to the strategic state, so no blocker for RESOLVE_BLOCKER to score


def test_a_ready_attack_is_unchanged():
    ent = _route(readiness=100.0).entity_updates[1]
    assert ent.task.payload_set.get("outcome") == "SUCCESS"
