import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, BuildingState, InteractionComponent, RegionState
from src_legacy.systems.guild_system import GuildIntelSystem

def test_guild_intel_emission():
    # Setup entity at guild
    entity = EntityState(
        id=1, kind="HERO", position=(10, 10),
        interaction=InteractionComponent(target_node_id=1, progress=9.0),
        properties={"interaction_kind": "guild"}
    )
    
    # Setup guild building
    guild = BuildingState(id=1, kind="guild", position=(10, 10))
    
    # Setup a high-trauma region
    danger_zone = RegionState(
        id="danger_1", name="Danger Zone", 
        bounds=(50, 50, 100, 100),
        trauma_score=10.0 # High trauma
    )
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={1: guild},
        regions={"danger_1": danger_zone}
    )
    
    # Run system
    update = GuildIntelSystem.update(state)
    
    # Verify strategic updates
    ent_upd = update.entity_updates[1]
    assert len(ent_upd.strategic.leads_add_or_update) == 1
    lead = ent_upd.strategic.leads_add_or_update[0]
    assert lead.subject == "danger_1"
    from src_legacy.core.strategic import LeadCertainty
    assert lead.certainty == LeadCertainty.APPROXIMATE
    
    # Verify concern creation
    assert len(ent_upd.strategic.concerns_add_or_update) == 1
    concern = ent_upd.strategic.concerns_add_or_update[0]
    assert concern.kind == "danger"
    assert concern.urgency == 1.0 # 10.0 / 10.0
