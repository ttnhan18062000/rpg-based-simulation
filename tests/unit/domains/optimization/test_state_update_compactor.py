import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate, InventoryUpdate
from src.engine.compactor import StateUpdateCompactor, CompactionMetrics
from src.engine.apply import ApplyPath


@pytest.fixture
def base_state() -> AuthoritativeState:
    e1 = V2EntityBuilder(1).kind("ACTOR").location(10.0, 20.0).build()
    e2 = (
        V2EntityBuilder(2)
        .kind("MERCHANT")
        .location(30.0, 40.0)
        .identity(properties={"title": "Vendor", "mood": "Calm"})
        .build()
    )
    return AuthoritativeState(tick=100, seed=42, world_time=100, entities={1: e1, 2: e2})


def test_compactor_drops_empty_entity_update(base_state: AuthoritativeState):
    """5.1 Drop no-op entity update."""
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)})
    compacted = StateUpdateCompactor.compact(base_state, update)
    assert 1 not in compacted.entity_updates


def test_compactor_drops_zero_delta_combat_update(base_state: AuthoritativeState):
    """5.2 Drop zero-delta combat update."""
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=0, max_hp_delta=0))
        }
    )
    compacted = StateUpdateCompactor.compact(base_state, update)
    assert 1 not in compacted.entity_updates


def test_compactor_preserves_nonzero_combat_update(base_state: AuthoritativeState):
    """5.3 Preserve meaningful combat update."""
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-10))
        }
    )
    compacted = StateUpdateCompactor.compact(base_state, update)
    assert 1 in compacted.entity_updates
    assert compacted.entity_updates[1].combat.hp_delta == -10


def test_compactor_drops_property_update_equal_to_current_value(base_state: AuthoritativeState):
    """5.4 Drop property update equal to current value."""
    entity = base_state.entities[2]

    update = StateUpdate(
        entity_updates={
            2: EntityUpdate(
                entity_id=2,
                kind_set=entity.kind,
                new_position=entity.navigation.position,
                property_updates={"title": "Vendor", "mood": "Calm"},
            )
        }
    )
    compacted, metrics = StateUpdateCompactor.compact_with_metrics(base_state, update)
    assert 2 not in compacted.entity_updates
    assert metrics.property_prunings == 4
    assert metrics.dropped_noop_updates == 1


def test_compacted_update_applies_same_as_uncompacted_update(base_state: AuthoritativeState):
    """5.5 Compacted apply equals uncompacted apply."""
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                combat=CombatUpdate(hp_delta=-15),
                inventory=InventoryUpdate(gold_delta=0),  # No-op subcomponent
            ),
            2: EntityUpdate(entity_id=2, kind_set="MERCHANT"),  # No-op property
        }
    )

    uncompacted_state = ApplyPath.apply_generation(base_state, update)
    compacted = StateUpdateCompactor.compact(base_state, update)
    compacted_state = ApplyPath.apply_generation(base_state, compacted)

    assert uncompacted_state.fingerprint() == compacted_state.fingerprint()


def test_compactor_reports_reduction_metrics(base_state: AuthoritativeState):
    """5.6 Compactor reports reduction metrics."""
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1),  # Dropped
            2: EntityUpdate(
                entity_id=2, kind_set="MERCHANT", combat=CombatUpdate(hp_delta=-5)
            ),  # Kind pruned, combat kept
        }
    )

    compacted, metrics = StateUpdateCompactor.compact_with_metrics(base_state, update)

    assert metrics.raw_entity_updates == 2
    assert metrics.compacted_entity_updates == 1
    assert metrics.dropped_noop_updates == 1
    assert metrics.property_prunings == 1
