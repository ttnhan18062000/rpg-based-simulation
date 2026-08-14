import pytest
from src.core.state import AuthoritativeState, ResourceNodeState, RegionState
from src.core.builder import V2EntityBuilder
from src.town.guild import GuildAction
from src.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_guild_visit_leads():
    # 1. Setup: World with iron node
    node = ResourceNodeState(id=1, kind="iron", position=(50, 50), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=10)
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(0, 0)
        .strategic()
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity}, resource_nodes={1: node})
    
    # 2. Guild Visit
    upd = GuildAction.visit(entity, state)
    assert upd is not None
    assert 99 in upd.entity_updates
    strat_upd = upd.entity_updates[99].strategic
    assert len(strat_upd.leads_add_or_update) > 0
    assert strat_upd.leads_add_or_update[0].subject == "iron_ore"
    
    # 3. Apply
    state = ApplyPath.apply_generation(state, upd)
    assert len(state.entities[99].strategic.leads) > 0

@pytest.mark.v2_contract
def test_guild_visit_quests():
    # 1. Setup
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(0, 0)
        .strategic()
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity})
    
    # 2. Guild Visit
    upd = GuildAction.visit(entity, state)
    assert upd is not None
    strat_upd = upd.entity_updates[99].strategic
    assert len(strat_upd.projects_add_or_update) == 1
    assert strat_upd.projects_add_or_update[0].kind == "quest"
    
    # 3. Apply
    state = ApplyPath.apply_generation(state, upd)
    assert len(state.entities[99].strategic.projects) == 1

@pytest.mark.v2_contract
def test_guild_visit_determinism():
    # 1. Setup: Same state, same entity
    node = ResourceNodeState(id=1, kind="iron", position=(50, 50), yields_item="iron_ore", remaining_charges=10, max_charges=10, required_ticks=10)
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(0, 0)
        .strategic()
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity}, resource_nodes={1: node})
    
    # 2. Multiple visits in same tick/seed should be identical
    upd1 = GuildAction.visit(entity, state)
    upd2 = GuildAction.visit(entity, state)
    
    lead1 = upd1.entity_updates[99].strategic.leads_add_or_update[0]
    lead2 = upd2.entity_updates[99].strategic.leads_add_or_update[0]

    assert lead1.id == lead2.id


@pytest.mark.v2_contract
def test_guild_visit_quest_reflects_region_pressure():
    # 1. Setup: entity located in a region with high trauma (above the 50.0
    # instability threshold, normalizes to 1.0), no resource nodes.
    region = RegionState(id="dark_forest", name="Dark Forest", bounds=(0, 0, 10, 10), trauma_score=60.0)
    entity = (V2EntityBuilder(99)
        .kind("hero")
        .location(0, 0)
        .navigation(region_id="dark_forest")
        .strategic()
        .build())
    state = AuthoritativeState(tick=1, seed=42, entities={99: entity}, regions={"dark_forest": region})

    # 2. Guild Visit
    upd = GuildAction.visit(entity, state)
    assert upd is not None
    strat_upd = upd.entity_updates[99].strategic
    assert len(strat_upd.projects_add_or_update) == 1
    assert strat_upd.projects_add_or_update[0].kind == "quest"
