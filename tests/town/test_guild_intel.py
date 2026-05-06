import pytest
from src.core.state import AuthoritativeState, BuildingState, RegionState
from src.core.builder import V2EntityBuilder
from src.systems.guild_system import GuildIntelSystem

def test_guild_intel_emission():
    # Setup entity at guild
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(10, 10)
        .with_interaction(target_id=1, progress=9.0)
        .with_property("interaction_kind", "guild")
        .build())
    
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
    from src.core.strategic import LeadCertainty
    assert lead.certainty == LeadCertainty.APPROXIMATE
    
    # Verify concern creation
    assert len(ent_upd.strategic.concerns_add_or_update) == 1
    concern = ent_upd.strategic.concerns_add_or_update[0]
    assert concern.kind == "danger"
    assert concern.urgency == 1.0 # 10.0 / 10.0
