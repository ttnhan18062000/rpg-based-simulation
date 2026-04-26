import pytest
from src.core.state import (
    AuthoritativeState, EntityState, BuildingState, 
    InteractionComponent, BiologicalComponent, InventoryComponent, CombatComponent
)
from src.systems.town_service import TownServiceSystem

def test_inn_restoration():
    # Setup entity with needs
    entity = EntityState(
        id=1, kind="HERO", position=(10, 10),
        biological=BiologicalComponent(sleep_debt=80.0, hunger=20.0),
        inventory=InventoryComponent(gold=100),
        combat=CombatComponent(hp=10, max_hp=100),
        interaction=InteractionComponent(target_node_id=1, progress=9.0),
        properties={"interaction_kind": "inn"}
    )
    
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
    assert ent_upd.biological.sleep_debt_set == 0.0
    assert ent_upd.combat.hp_delta == 100
    assert ent_upd.inventory.gold_delta == -10
    assert ent_upd.interaction.reset == True

def test_tavern_nourishment():
    entity = EntityState(
        id=1, kind="HERO", position=(10, 10),
        biological=BiologicalComponent(hunger=90.0),
        inventory=InventoryComponent(gold=50),
        interaction=InteractionComponent(target_node_id=2, progress=9.0),
        properties={"interaction_kind": "tavern"}
    )
    
    tavern = BuildingState(id=2, kind="tavern", position=(10, 10))
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={2: tavern}
    )
    
    update = TownServiceSystem.update(state)
    
    ent_upd = update.entity_updates[1]
    assert ent_upd.biological.hunger_set == 0.0
    assert ent_upd.inventory.gold_delta == -5
