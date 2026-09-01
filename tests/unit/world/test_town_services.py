import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, BuildingState
from src.core.builder import V2EntityBuilder
from src.systems.town_service import TownServiceSystem

def test_inn_restoration():
    # Setup entity with needs
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(10.0, 10.0)
        .biological(sleep_debt=80.0, hunger=20.0)
        .inventory(gold=100)
        .combat(hp=10, max_hp=100)
        .interaction(target_node_id=1, progress=9.0)
        .build())
    entity = replace(entity, interaction=replace(entity.interaction, kind="inn"))
    
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
        .kind("hero")
        .location(10.0, 10.0)
        .biological(hunger=90.0)
        .inventory(gold=50)
        .combat(hp=10, max_hp=100)
        .interaction(target_node_id=2, progress=9.0)
        .build())
    entity = replace(entity, interaction=replace(entity.interaction, kind="tavern"))
    
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

def test_guild_service_routes_via_interaction_kind():
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(10.0, 10.0)
        .interaction(target_node_id=3, progress=9.0)
        .build())
    entity = replace(entity, interaction=replace(entity.interaction, kind="guild"))

    guild = BuildingState(id=3, kind="guild", position=(10, 10))

    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={3: guild}
    )

    update = TownServiceSystem.update(state)

    ent_upd = update.entity_updates[1]
    assert ent_upd.interaction.reset == True
    assert ent_upd.property_updates.get("visited_guild_tick") == 100

def test_unrelated_interaction_kind_not_routed():
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(10.0, 10.0)
        .interaction(target_node_id=1, progress=9.0)
        .build())
    entity = replace(entity, interaction=replace(entity.interaction, kind="harvest"))

    inn = BuildingState(id=1, kind="inn", position=(10, 10))

    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={1: inn}
    )

    update = TownServiceSystem.update(state)

    assert 1 not in update.entity_updates
