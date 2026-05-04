import pytest
from src.core.state import AuthoritativeState, BuildingState
from src.core.builder import V2EntityBuilder
from src.systems.town_service import TownServiceSystem

def test_inn_restoration():
    # Setup entity with needs
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .at((10, 10))
        .with_biological(sleep_debt=80.0, hunger=20.0)
        .gold(100)
        .with_combat(hp=10, max_hp=100)
        .with_interaction(target_id=1, progress=9.0)
        .with_property("interaction_kind", "inn")
        .build())
    
    # Setup inn building
    inn = BuildingState(id=1, kind="inn", position=(10, 10))
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={1: inn}
    )
    
    # Run system
    update = TownServiceSystem.update(state)
    
    # Verify completion update
    ent_upd = update.entity_updates[1]
    assert len(ent_upd.resource_transfers) == 1
    intent = ent_upd.resource_transfers[0]
    assert intent.biological_upd.sleep_debt_set == 0.0
    assert intent.combat_upd.hp_delta == entity.combat.max_hp
    assert intent.gold_delta == -10
    assert ent_upd.interaction.reset == True

def test_tavern_nourishment():
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .at((10, 10))
        .with_biological(hunger=90.0)
        .gold(50)
        .with_interaction(target_id=2, progress=9.0)
        .with_property("interaction_kind", "tavern")
        .build())
    
    tavern = BuildingState(id=2, kind="tavern", position=(10, 10))
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={2: tavern}
    )
    
    update = TownServiceSystem.update(state)
    
    ent_upd = update.entity_updates[1]
    assert len(ent_upd.resource_transfers) == 1
    intent = ent_upd.resource_transfers[0]
    assert intent.biological_upd.hunger_set == 0.0
    assert intent.gold_delta == -5
