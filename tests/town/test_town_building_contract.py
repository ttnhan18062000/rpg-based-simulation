import pytest
from src.core.state import AuthoritativeState, BuildingState
from src.core.builder import V2EntityBuilder
from src.town.buildings import BuildingRegistry
from src.town.town_navigation import TownNavigation

@pytest.mark.v2_contract
def test_building_registry_templates():
    # 1. Verify static data
    inn_services = BuildingRegistry.get_services(BuildingRegistry.INN)
    assert "REST" in inn_services
    assert "HEAL_DEBT" in inn_services
    
    guild_services = BuildingRegistry.get_services(BuildingRegistry.GUILD)
    assert "QUEST" in guild_services

@pytest.mark.v2_contract
def test_town_navigation_service_lookup():
    # 1. Setup: State with two shops
    shop1 = BuildingState(id=1, kind=BuildingRegistry.SHOP, position=(10, 10))
    shop2 = BuildingState(id=2, kind=BuildingRegistry.SHOP, position=(100, 100))
    state = AuthoritativeState(
        tick=1, 
        seed=42, 
        buildings={1: shop1, 2: shop2},
        town_center=(0, 0)
    )
    
    # 2. Entity at (5, 5) should find shop1
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(5, 5)
        .build())
    nearest = TownNavigation.get_nearest_service(entity, BuildingRegistry.SHOP, state)
    assert nearest is not None
    assert nearest.id == 1
    
    # 3. Entity at (110, 110) should find shop2
    entity2 = (V2EntityBuilder(100)
        .kind("hero")
        .location(110, 110)
        .build())
    nearest2 = TownNavigation.get_nearest_service(entity2, BuildingRegistry.SHOP, state)
    assert nearest2 is not None
    assert nearest2.id == 2

@pytest.mark.v2_contract
def test_town_navigation_proximity():
    state = AuthoritativeState(tick=1, seed=42, town_center=(0, 0))
    
    # 1. In town
    ent_in = (V2EntityBuilder(1)
        .kind("hero")
        .location(10, 10)
        .build())
    assert TownNavigation.is_in_town(ent_in, state) == True
    
    # 2. Out of town
    ent_out = (V2EntityBuilder(2)
        .kind("hero")
        .location(100, 100)
        .build())
    assert TownNavigation.is_in_town(ent_out, state) == False

@pytest.mark.v2_contract
def test_functional_building_requirement():
    # 1. Setup: Shop is non-functional
    shop = BuildingState(id=1, kind=BuildingRegistry.SHOP, position=(10, 10), functional=False)
    state = AuthoritativeState(tick=1, seed=42, buildings={1: shop})
    
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(0, 0)
        .build())
    nearest = TownNavigation.get_nearest_service(entity, BuildingRegistry.SHOP, state)
    
    # 2. Should find nothing
    assert nearest is None
