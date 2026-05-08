from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline


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
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def test_occupancy_conflict_resolution():
    """
    LAW:
        If two active entities claim the same destination tile in the same
        authoritative update, the conflict must resolve deterministically.

    Scenario:
        Entity 1 starts at (0, 0).
        Entity 2 starts at (2, 0).
        Both propose moving to (1, 0).

    Expected:
        Entity 1 wins because it has the lower entity id.
        Entity 2 loses and its movement is rejected.

    Fraud this catches:
        - two entities can occupy the same final tile
        - conflict winner depends on dictionary iteration order
        - raw worker-proposed new_position bypasses authoritative validation
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

    raw_update = StateUpdate(
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

    refined_update = AuthoritativeApplyPipeline.refine(
        state,
        raw_update,
    )

    assert refined_update.entity_updates[1].new_position == (1.0, 0.0)

    rejected_update = refined_update.entity_updates[2]
    assert rejected_update.new_position is None
    assert rejected_update.moved_this_tick is False
    assert rejected_update.navigation is not None
    assert rejected_update.navigation.failure_reason == "OCCUPANCY_CONFLICT"


def test_occupancy_conflict_with_static_entity():
    """
    LAW:
        An entity must not move into a tile occupied by another active entity
        that is not moving away during the same authoritative update.

    Scenario:
        Entity 1 starts at (0, 0).
        Entity 2 is already standing at (1, 0).
        Entity 1 proposes moving to (1, 0).
        Entity 2 has no movement proposal.

    Expected:
        Entity 1's move is rejected because the target tile is statically
        occupied by Entity 2.

    Fraud this catches:
        - movement into occupied static tiles is allowed
        - raw new_position proposals bypass movement legality
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

    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                new_position=(1.0, 0.0),
                moved_this_tick=True,
            )
        }
    )

    refined_update = AuthoritativeApplyPipeline.refine(
        state,
        raw_update,
    )

    rejected_update = refined_update.entity_updates[1]
    assert rejected_update.new_position is None
    assert rejected_update.moved_this_tick is False
    assert rejected_update.navigation is not None
    assert rejected_update.navigation.failure_reason == "OCCUPANCY_CONFLICT"