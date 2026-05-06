import pytest
from src.core.state import AuthoritativeState, BuildingState, RegionState, CombatComponent
from src.core.builder import V2EntityBuilder
from src.town.sabotage import SabotageAction
from src.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_building_sabotage_damage():
    # 1. Setup: Building at (10, 10), entity at (11, 11)
    building = BuildingState(id=1, kind="SHOP", position=(10, 10), hp=100)
    entity = (V2EntityBuilder(99)
        .kind("raider")
        .location(11, 11)
        .attributes(strength=0)
        .combat(atk=20)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity}, buildings={1: building})
    
    # 2. Sabotage
    upd = SabotageAction.apply(entity, 1, state)
    assert upd is not None
    assert 1 in upd.building_updates
    assert upd.building_updates[1].hp_delta == -20
    
    # 3. Apply
    next_state = ApplyPath.apply_generation(state, upd)
    assert next_state.buildings[1].hp == 80
    assert next_state.buildings[1].functional == True

@pytest.mark.v2_contract
def test_building_destruction_and_trauma():
    # 1. Setup: Building with 10 HP, entity with 20 ATK in region "town"
    building = BuildingState(id=1, kind="INN", position=(10, 10), hp=10)
    region = RegionState(id="town", name="Town", bounds=(0, 0, 100, 100), trauma_score=0.0)
    entity = (V2EntityBuilder(99)
        .kind("raider")
        .location(10, 10)
        .attributes(strength=0)
        .combat(atk=20)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity}, buildings={1: building}, regions={"town": region})
    
    # 2. Destroy Building
    upd = SabotageAction.apply(entity, 1, state)
    
    # 3. Apply
    next_state = ApplyPath.apply_generation(state, upd)
    assert next_state.buildings[1].hp == 0
    assert next_state.buildings[1].functional == False
    
    # 4. Trauma Verification (2.0 increment)
    assert next_state.regions["town"].trauma_score == 2.0

@pytest.mark.v2_contract
def test_sabotage_proximity_validation():
    # 1. Setup: Entity far away (50, 50)
    building = BuildingState(id=1, kind="SHOP", position=(0, 0), hp=100)
    entity = (V2EntityBuilder(99)
        .kind("raider")
        .location(50, 50)
        .attributes(strength=0)
        .combat(atk=0)
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity}, buildings={1: building})
    
    # 2. Sabotage should fail
    upd = SabotageAction.apply(entity, 1, state)
    assert upd is None
