"""TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED: an INTERACT whose resource node is gone or has
no charges left can never gather anything, so ActionRoutingPhase.route() ends the held task and hands the entity back to the brain,
the same class as ATTACK with TARGET_INCAPACITATED / OUT_OF_RANGE. Before, the scheduler re-ran the held ENTITY_ACT every tick with
outcome SUCCESS for hundreds of ticks while the entity starved beside food it carried.

PR 2 only releases the subject: it adds no hunger or food logic."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.state import AuthoritativeState, ResourceNodeState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.cadence import SystemCadence, should_run
from src.engine.pipeline_phases.actions import ActionRoutingPhase, _is_unrecoverable_action_failure
from src.engine.scheduler import DeterministicScheduler

NODE_ID = 10002


def _gatherer():
    return V2EntityBuilder(1).kind("worker").location(10.0, 10.0).combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build()


def _node(charges):
    return ResourceNodeState(
        id=NODE_ID, kind="berry_thicket", position=(10.0, 11.0), yields_item="herb", remaining_charges=charges, max_charges=8, required_ticks=1)


def _interact(entity_id=1, target=NODE_ID):
    return StateUpdate(entity_updates={entity_id: EntityUpdate(
        entity_id=entity_id, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "INTERACT", "target_id": target}))})


def _route(nodes):
    state = AuthoritativeState(tick=1, seed=42, entities={1: _gatherer()}, resource_nodes=nodes)
    return ActionRoutingPhase.route(state, _interact())


@pytest.mark.parametrize("nodes,reason", [
    ({NODE_ID: _node(0)}, ReasonCode.SOURCE_DEPLETED),
    ({}, ReasonCode.SOURCE_MISSING),
], ids=["zero_charges", "node_missing"])
def test_interact_on_a_depleted_or_missing_node_ends_the_held_task(nodes, reason):
    refined = _route(nodes)
    upd = refined.entity_updates[1]
    assert upd.task.payload_set == {}  # an empty payload is what hands the entity back to the brain (scheduler is_idle_act)
    assert [(e.actor_id, e.action_kind, e.reason) for e in refined.rejection_events] == [(1, "INTERACT", reason.value)]


def test_interact_on_a_node_with_charges_is_held_as_before():
    refined = _route({NODE_ID: _node(3)})
    upd = refined.entity_updates[1]
    assert upd.task.payload_set["action"] == "INTERACT" and upd.task.payload_set["outcome"] == "SUCCESS"
    assert not refined.rejection_events


def test_a_released_gatherer_is_scheduled_for_the_brain_on_its_next_cadence_tick():
    entity = _gatherer()
    held = replace(entity, task=replace(entity.task, work_kind="ENTITY_ACT", payload={"action": "INTERACT", "target_id": NODE_ID, "outcome": "SUCCESS"}))
    released = replace(held, task=replace(held.task, payload={}))
    cadence = SystemCadence().strategic_intelligence
    tick = next(t for t in range(1, 1000) if should_run(t, entity.id, cadence))

    def kinds(ent):
        state = AuthoritativeState(tick=tick, seed=42, entities={1: ent}, resource_nodes={NODE_ID: _node(0)})
        work, _ = DeterministicScheduler().select_work(state)
        return [w.work_kind for w in work if w.owner_id == 1]

    assert kinds(held) == ["ENTITY_ACT"]  # the bug: the held no-op is re-dispatched, the brain never runs
    assert kinds(released) == ["ENTITY_BRAIN"]


def test_only_depletion_reasons_end_a_held_interact():
    assert _is_unrecoverable_action_failure("INTERACT", "FAILURE", ReasonCode.SOURCE_DEPLETED.value)
    assert _is_unrecoverable_action_failure("INTERACT", "FAILURE", ReasonCode.SOURCE_MISSING.value)
    assert not _is_unrecoverable_action_failure("INTERACT", "FAILURE", ReasonCode.INSUFFICIENT_READINESS.value)
    assert not _is_unrecoverable_action_failure("ATTACK", "FAILURE", ReasonCode.SOURCE_DEPLETED.value)  # ATTACK keeps its own list
    assert _is_unrecoverable_action_failure("ATTACK", "FAILURE", ReasonCode.OUT_OF_RANGE.value)
