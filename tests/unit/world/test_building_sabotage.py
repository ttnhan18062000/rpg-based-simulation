import pytest
from src.core.state import AuthoritativeState, BuildingState, RegionState
from src.core.builder import V2EntityBuilder
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.apply import ApplyPath
from src.engine.sabotage import BuildingSabotageSystem


def _sabotaging_entity(entity_id: int, position: tuple) -> object:
    return (
        V2EntityBuilder(entity_id)
        .kind("raider")
        .location(*position)
        .attributes(strength=0)
        .combat(atk=20)
        .lifecycle(active=True)
        .build()
    )


def _sabotage_intent_update(entity_id: int, target_pos: tuple) -> StateUpdate:
    return StateUpdate(
        entity_updates={
            entity_id: EntityUpdate(
                entity_id=entity_id,
                task=TaskUpdate(
                    work_kind_set="SABOTAGE",
                    payload_set={"target_pos": target_pos},
                ),
            )
        }
    )


@pytest.mark.v2_contract
def test_building_sabotage_damage():
    # 1. Setup: Building at (10, 10), entity within proximity range.
    building = BuildingState(id=1, kind="SHOP", position=(10, 10), hp=100)
    entity = _sabotaging_entity(99, (10, 10))
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity}, buildings={1: building})
    upd = _sabotage_intent_update(99, (10, 10))

    # 2. Resolve sabotage
    refined = BuildingSabotageSystem.resolve(state, upd)
    assert 1 in refined.building_updates
    assert refined.building_updates[1].hp_delta == -50

    # 3. Apply
    next_state = ApplyPath.apply_generation(state, refined)
    assert next_state.buildings[1].hp == 50
    assert next_state.buildings[1].functional is True


@pytest.mark.v2_contract
def test_building_destruction_and_trauma():
    # 1. Setup: Building with 10 HP, entity in region "town".
    building = BuildingState(id=1, kind="INN", position=(10, 10), hp=10)
    region = RegionState(id="town", name="Town", bounds=(0, 0, 100, 100), trauma_score=0.0)
    entity = _sabotaging_entity(99, (10, 10))
    state = AuthoritativeState(
        tick=1, seed=42, entities={99: entity}, buildings={1: building}, regions={"town": region}
    )
    upd = _sabotage_intent_update(99, (10, 10))

    # 2. Resolve sabotage
    refined = BuildingSabotageSystem.resolve(state, upd)

    # 3. Apply
    next_state = ApplyPath.apply_generation(state, refined)
    assert next_state.buildings[1].hp == 0
    assert next_state.buildings[1].functional is False

    # 4. Trauma verification (2.0 increment)
    assert next_state.regions["town"].trauma_score == 2.0


@pytest.mark.v2_contract
def test_sabotage_proximity_validation():
    # 1. Setup: Entity far away from target position.
    building = BuildingState(id=1, kind="SHOP", position=(0, 0), hp=100)
    entity = _sabotaging_entity(99, (50, 50))
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity}, buildings={1: building})
    upd = _sabotage_intent_update(99, (0, 0))

    # 2. Sabotage should be rejected — target out of proximity range.
    refined = BuildingSabotageSystem.resolve(state, upd)
    assert refined.building_updates == {}
    assert refined.rejections_delta.get("SABOTAGE_OUT_OF_RANGE") == 1
