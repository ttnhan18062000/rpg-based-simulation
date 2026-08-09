"""TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE: route_movement_intent must re-derive a live
navigation target from task.payload["target_id"] when relying on a persisted (potentially stale)
navigation.target snapshot, rather than blindly walking toward a fixed point the target has
long since moved away from. See stored_artifacts/TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE/
investigation.md for the real per-tick trace that found this.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.engine.pipeline_phases.movement import MovementPhase


def _pursuer(entity_id, pos, nav_target, target_id):
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .navigation(target=nav_target, movement_mode=MovementMode.PURSUE)
        .task(work_kind="ENTITY_MOVE", payload={"target_id": target_id, "target_position": nav_target})
        .build()
    )


def _target(entity_id, pos, alive=True, active=True):
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .combat(hp=100, max_hp=100, alive=alive, readiness=100.0)
        .lifecycle(active=active)
        .build()
    )


def test_pursuit_target_refreshes_to_live_position_not_stale_snapshot():
    # Stale nav_target (10, 20) is north of the pursuer; the real, live target has since moved
    # to (10, 0), south of the pursuer. If the fix works, the pursuer steps south (y decreases).
    pursuer = _pursuer(1, (10.0, 10.0), nav_target=(10.0, 20.0), target_id=2)
    target = _target(2, (10.0, 0.0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: pursuer, 2: target})

    refined = MovementPhase.route_movement_intent(state, StateUpdate())

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.new_position is not None
    assert upd.new_position[1] < 10.0, (
        f"expected pursuer to step toward the live target position (y<10), "
        f"got {upd.new_position} -- fix did not refresh the stale snapshot"
    )


def test_fixed_point_errand_not_refreshed_without_target_id():
    """WANDER/RETREAT/objective-pursuit never set task.payload['target_id'] -- confirms the fix
    is a no-op for genuine fixed-point movement, not just for lack of a live entity. A live entity
    2 sits at (10, 0) (south) but is irrelevant here since no target_id references it -- the
    entity must still walk toward the static (10, 20) point (north, y>10)."""
    entity = (
        V2EntityBuilder(1)
        .kind("monster")
        .location(10.0, 10.0)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .navigation(target=(10.0, 20.0), movement_mode=MovementMode.PURSUE)
        .task(work_kind="ENTITY_MOVE", payload={"target_position": (10.0, 20.0)})
        .build()
    )
    decoy = _target(2, (10.0, 0.0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity, 2: decoy})

    refined = MovementPhase.route_movement_intent(state, StateUpdate())

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.new_position is not None
    assert upd.new_position[1] > 10.0, "fixed-point errand should still move toward the static target (y>10)"


def test_dead_target_id_falls_back_to_stale_snapshot_without_crashing():
    pursuer = _pursuer(1, (10.0, 10.0), nav_target=(10.0, 20.0), target_id=2)
    dead_target = _target(2, (10.0, 0.0), alive=False)
    state = AuthoritativeState(tick=1, seed=42, entities={1: pursuer, 2: dead_target})

    refined = MovementPhase.route_movement_intent(state, StateUpdate())

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.new_position is not None
    assert upd.new_position[1] > 10.0, "a dead target_id must not be tracked -- falls back to the static snapshot"


def test_missing_target_id_entity_falls_back_to_stale_snapshot_without_crashing():
    pursuer = _pursuer(1, (10.0, 10.0), nav_target=(10.0, 20.0), target_id=999)
    state = AuthoritativeState(tick=1, seed=42, entities={1: pursuer})

    refined = MovementPhase.route_movement_intent(state, StateUpdate())

    upd = refined.entity_updates.get(1)
    assert upd is not None
    assert upd.new_position is not None
    assert upd.new_position[1] > 10.0
