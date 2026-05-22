from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate
from src.engine.pipeline_phases.occupancy import OccupancyPhase


def make_actor(
    entity_id: int,
    pos: tuple[float, float],
):
    """
    Build a minimal active entity for occupancy-conflict tests.

    The helper intentionally uses V2EntityBuilder instead of raw EntityState so
    the entity has modern navigation/lifecycle/combat components initialized in
    the same way as normal runtime entities.
    """
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(float(pos[0]), float(pos[1]))
        .combat(
            hp=100,
            max_hp=100,
            alive=True,
            readiness=100.0,
        )
        .lifecycle(active=True)
        .build()
    )


def test_occupancy_conflict_resolution():
    """
    LAW:
        If two active entities claim the same destination tile in the same
        authoritative movement result, the conflict must resolve
        deterministically.

    Scope:
        This is an OccupancyPhase test, not a full-pipeline trust-boundary test.

    Why this calls OccupancyPhase directly:
        AuthoritativeApplyPipeline.refine(...) begins with TrustBoundaryPhase.
        Raw worker proposals are not allowed to directly set new_position, so
        full pipeline would reject these updates as UNTRUSTED_DIRECT_MOVEMENT
        before occupancy can inspect them.

        This test intentionally passes already-authoritative movement results
        directly into OccupancyPhase.

    Scenario:
        Entity 1 starts at (0, 0).
        Entity 2 starts at (2, 0).
        Both authoritative movement results claim (1, 0).

    Expected:
        Entity 1 wins because it has the lower entity id.
        Entity 2 loses and receives OCCUPANCY_CONFLICT.

    Fraud this catches:
        - two entities can occupy the same final tile
        - conflict winner depends on dictionary iteration order
        - occupancy phase fails to deterministically reject loser
    """
    ent1 = make_actor(1, pos=(0.0, 0.0))
    ent2 = make_actor(2, pos=(2.0, 0.0))

    state = AuthoritativeState(
        tick=0,
        seed=1,
        entities={
            1: ent1,
            2: ent2,
        },
    )

    authoritative_movement_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                new_position=(1.0, 0.0),
                moved_this_tick=True,
            ),
            2: EntityUpdate(
                entity_id=2,
                new_position=(1.0, 0.0),
                moved_this_tick=True,
            ),
        }
    )

    refined_update = OccupancyPhase.resolve(
        state,
        authoritative_movement_update,
    )

    winning_update = refined_update.entity_updates[1]
    assert winning_update.new_position == (1.0, 0.0)
    assert winning_update.moved_this_tick is True

    rejected_update = refined_update.entity_updates[2]
    assert rejected_update.new_position is None
    assert rejected_update.moved_this_tick is False
    assert rejected_update.navigation is not None
    assert rejected_update.navigation.failure_reason == "OCCUPANCY_CONFLICT"

    assert refined_update.rejections_delta.get("OCCUPANCY_CONFLICT", 0) == 1

    assert any(
        event.actor_id == 2
        and event.action_kind == "MOVE"
        and event.reason == "OCCUPANCY_CONFLICT"
        for event in refined_update.rejection_events
    )


def test_occupancy_conflict_with_static_entity():
    """
    LAW:
        An entity must not move into a tile occupied by another active entity
        that is not moving away during the same authoritative movement result.

    Scope:
        This is an OccupancyPhase test, not a full-pipeline trust-boundary test.

    Why this calls OccupancyPhase directly:
        Full pipeline rejects raw direct new_position proposals at the trust
        boundary. OCCUPANCY_CONFLICT only applies after an authoritative movement
        phase has produced final movement results.

    Scenario:
        Entity 1 starts at (0, 0).
        Entity 2 is already standing at (1, 0).
        Entity 1's authoritative movement result claims (1, 0).
        Entity 2 has no movement result.

    Expected:
        Entity 1's move is rejected because the target tile is statically
        occupied by Entity 2.

    Fraud this catches:
        - movement into occupied static tiles is allowed
        - occupancy phase ignores stationary active entities
        - final apply path can commit overlapping entity positions
    """
    ent1 = make_actor(1, pos=(0.0, 0.0))
    ent2 = make_actor(2, pos=(1.0, 0.0))

    state = AuthoritativeState(
        tick=0,
        seed=1,
        entities={
            1: ent1,
            2: ent2,
        },
    )

    authoritative_movement_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                new_position=(1.0, 0.0),
                moved_this_tick=True,
            )
        }
    )

    refined_update = OccupancyPhase.resolve(
        state,
        authoritative_movement_update,
    )

    rejected_update = refined_update.entity_updates[1]

    assert rejected_update.new_position is None
    assert rejected_update.moved_this_tick is False
    assert rejected_update.navigation is not None
    assert rejected_update.navigation.failure_reason == "OCCUPANCY_CONFLICT"

    assert refined_update.rejections_delta.get("OCCUPANCY_CONFLICT", 0) == 1

    assert any(
        event.actor_id == 1
        and event.action_kind == "MOVE"
        and event.reason == "OCCUPANCY_CONFLICT"
        for event in refined_update.rejection_events
    )


def test_cascading_occupancy_rejection():
    """
    LAW:
        If Entity B (209) is rejected from moving to Tile Y because Tile Y is occupied
        by static Entity C (208), then Entity A (210) trying to move to Entity B's
        start-of-tick Tile X must also be rejected.
    """
    ent1 = make_actor(1, pos=(0.0, 0.0))
    ent2 = make_actor(2, pos=(1.0, 0.0))
    ent3 = make_actor(3, pos=(2.0, 0.0))

    state = AuthoritativeState(
        tick=0,
        seed=1,
        entities={
            1: ent1,
            2: ent2,
            3: ent3,
        },
    )

    # Ent 1 (210 equivalent) claims Ent 2's start-of-tick tile (1.0, 0.0)
    # Ent 2 (209 equivalent) claims Ent 3's start-of-tick tile (2.0, 0.0)
    # Ent 3 (208 equivalent) is static (no update)
    authoritative_movement_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                new_position=(1.0, 0.0),
                moved_this_tick=True,
            ),
            2: EntityUpdate(
                entity_id=2,
                new_position=(2.0, 0.0),
                moved_this_tick=True,
            ),
        }
    )

    refined_update = OccupancyPhase.resolve(
        state,
        authoritative_movement_update,
    )

    # Both Ent 1 and Ent 2 must be rejected
    rejected_update_1 = refined_update.entity_updates[1]
    assert rejected_update_1.new_position is None
    assert rejected_update_1.moved_this_tick is False
    assert rejected_update_1.navigation.failure_reason == "OCCUPANCY_CONFLICT"

    rejected_update_2 = refined_update.entity_updates[2]
    assert rejected_update_2.new_position is None
    assert rejected_update_2.moved_this_tick is False
    assert rejected_update_2.navigation.failure_reason == "OCCUPANCY_CONFLICT"

    assert refined_update.rejections_delta.get("OCCUPANCY_CONFLICT", 0) == 2