"""TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET: ActionRoutingPhase.route() must reset an
entity's task to idle when an ATTACK fails with TARGET_INCAPACITATED (an unrecoverable failure -
the target is dead/inactive and retrying the same target_id can never succeed), so the entity
becomes eligible for scheduler.py's own is_idle_act/brain-cadence gate again instead of getting
re-dispatched with the same stale target every tick readiness recovers.

Recoverable failures (INSUFFICIENT_READINESS, OUT_OF_RANGE) must NOT reset -- those legitimately
resolve on their own (readiness regen, a fresh pursuit decision) without losing the current
target lock.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.pipeline_phases.actions import ActionRoutingPhase


def _attacker_entity(entity_id: int, readiness: float = 100.0, attack_range: int = 10, pos=(10.0, 10.0)):
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .combat(hp=100, max_hp=100, alive=True, readiness=readiness, attack_range=attack_range)
        .lifecycle(active=True)
        .identity(faction=Faction.HERO_GUILD)
        .build()
    )


def _target_entity(entity_id: int, alive: bool = True, active: bool = True, pos=(10.0, 11.0)):
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .combat(hp=100, max_hp=100, alive=alive)
        .lifecycle(active=active)
        .identity(faction=Faction.MONSTER_HORDE)
        .build()
    )


def _attack_update(entity_id: int, target_id: int) -> StateUpdate:
    return StateUpdate(entity_updates={
        entity_id: EntityUpdate(
            entity_id=entity_id,
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": target_id}),
        )
    })


def test_attack_against_dead_target_resets_task_to_idle():
    attacker = _attacker_entity(1)
    dead_target = _target_entity(2, alive=False, active=False)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: dead_target})

    refined = ActionRoutingPhase.route(state, _attack_update(1, 2))

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.task is not None
    assert upd.task.payload_set == {}


def test_attack_against_incapacitated_but_alive_target_resets_task_to_idle():
    """TARGET_INCAPACITATED also covers lifecycle.active=False alone -- confirms the reset isn't
    narrowly tied to combat.alive specifically."""
    attacker = _attacker_entity(1)
    incapacitated_target = _target_entity(2, alive=True, active=False)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: incapacitated_target})

    refined = ActionRoutingPhase.route(state, _attack_update(1, 2))

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.task.payload_set == {}


def test_attack_with_insufficient_readiness_does_not_reset_task():
    attacker = _attacker_entity(1, readiness=0.0)
    alive_target = _target_entity(2, alive=True, active=True)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: alive_target})

    refined = ActionRoutingPhase.route(state, _attack_update(1, 2))

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.task.payload_set.get("target_id") == 2
    assert upd.task.payload_set.get("reason") == "INSUFFICIENT_READINESS"


def test_attack_out_of_range_does_not_reset_task():
    attacker = _attacker_entity(1, attack_range=1, pos=(0.0, 0.0))
    far_target = _target_entity(2, alive=True, active=True, pos=(50.0, 50.0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: far_target})

    refined = ActionRoutingPhase.route(state, _attack_update(1, 2))

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.task.payload_set.get("target_id") == 2
    assert upd.task.payload_set.get("reason") == "OUT_OF_RANGE"


def test_missing_action_kind_is_untouched():
    """A task update with no real 'action' key in payload is skipped entirely (route()'s own
    pre-existing `if not action: continue` short-circuit) -- confirms this fix's new condition
    doesn't get evaluated for non-action task updates."""
    attacker = _attacker_entity(1)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker})
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={}))
    })

    refined = ActionRoutingPhase.route(state, update)

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.task.payload_set == {}
