from src.core.builder import V2EntityBuilder
from src.core.cognition import CognitionModel, RoleModelBundle
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.strategy.role_model_imitation import RoleModelImitationService
from src.strategy.role_model_phase import RoleModelSelectionPhase


def build_entity(entity_id, x, y, evolution_level=1, cognition=None):
    builder = (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(x, y)
        .identity(evolution_level=evolution_level)
    )
    if cognition is not None:
        builder = builder.replace_cognition(cognition)
    return builder.build()


def test_role_model_lifecycle_add_and_clear():
    watcher = build_entity(1, 0.0, 0.0, evolution_level=1)
    admired = build_entity(2, 3.0, 4.0, evolution_level=5)  # distance 5 <= radius 10

    state = AuthoritativeState(tick=9, seed=1, entities={1: watcher, 2: admired})
    result = RoleModelSelectionPhase.apply(state, StateUpdate())

    role_model = result.entity_updates[1].cognition_bundle_set.role_model
    assert role_model.admired_entity_id == 2
    assert role_model.admired_since_tick == 9
    assert role_model.last_reconsidered_tick == 9

    # Second call, previously-admired entity removed from the world: implicit clear.
    watcher_after = build_entity(
        1, 0.0, 0.0, evolution_level=1,
        cognition=CognitionModel(role_model=role_model),
    )
    state_after = AuthoritativeState(tick=19, seed=1, entities={1: watcher_after})
    result_after = RoleModelSelectionPhase.apply(state_after, StateUpdate())

    role_model_after = result_after.entity_updates[1].cognition_bundle_set.role_model
    assert role_model_after.admired_entity_id is None
    assert role_model_after.last_reconsidered_tick == 19


def test_role_model_cadence_gating_skips_non_run_tick():
    watcher = build_entity(1, 0.0, 0.0, evolution_level=1)
    admired = build_entity(2, 3.0, 4.0, evolution_level=5)

    # tick=0 -> (0 + entity_id=1) % cadence(10) == 1 != 0 -> should_run is False for entity 1.
    state = AuthoritativeState(tick=0, seed=1, entities={1: watcher, 2: admired})
    result = RoleModelSelectionPhase.apply(state, StateUpdate())

    assert 1 not in result.entity_updates


def test_role_model_selection_stores_imitation_fidelity():
    watcher = build_entity(1, 0.0, 0.0, evolution_level=1)
    admired = build_entity(2, 3.0, 4.0, evolution_level=5)

    state = AuthoritativeState(tick=9, seed=1, entities={1: watcher, 2: admired})
    result = RoleModelSelectionPhase.apply(state, StateUpdate())

    role_model = result.entity_updates[1].cognition_bundle_set.role_model
    expected_fidelity = RoleModelImitationService.compute_imitation_fidelity(watcher)
    assert role_model.imitation_fidelity == expected_fidelity
