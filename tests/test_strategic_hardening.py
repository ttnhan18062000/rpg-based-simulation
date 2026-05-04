import pytest
from src.core.state import AuthoritativeState, EntityState, AttributeComponent, InventoryComponent, ItemStack, ResourceNodeState
from src.core.updates import StateUpdate, EntityUpdate, ResourceTransferIntent, InteractionUpdate, CombatUpdate, StrategicUpdate
from src.engine.interaction import InteractionSystem
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.strategic import StrategicComponent, CognitionProfile, LeadState, ConcernState
from src.core.enums import ReasonCode

def test_interaction_interrupted_by_damage():
    # Setup entity with interaction progress
    ent = EntityState(
        id=1,
        kind="HERO",
        position=(0, 0),
        combat=None, # will use default
        interaction=None # will use default (0 progress)
    )
    # Manually set progress
    from src.core.state import InteractionComponent
    ent = replace_interaction(ent, 5)
    
    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=100, kind="WOOD", position=(0,0), yields_item="WOOD", required_ticks=10, remaining_charges=10, max_charges=10)
    state = AuthoritativeState(tick=10, seed=42, entities={1: ent}, resource_nodes={100: node})
    
    # 1. Action without damage: progress continues
    upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, interaction=InteractionUpdate(progress_delta=1.0))
    })
    refined = InteractionSystem.enforce(state, upd)
    assert refined.entity_updates[1].interaction.reset is False
    
    # 2. Action with small damage (< 5% of 100 HP): progress continues
    upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, 
            interaction=InteractionUpdate(progress_delta=1.0),
            combat=CombatUpdate(damage_taken=2)
        )
    })
    refined = InteractionSystem.enforce(state, upd)
    assert refined.entity_updates[1].interaction.reset is False
    
    # 3. Action with large damage (> 5% of 100 HP): reset!
    upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, 
            interaction=InteractionUpdate(progress_delta=1.0),
            combat=CombatUpdate(damage_taken=10)
        )
    })
    refined = InteractionSystem.enforce(state, upd)
    assert refined.entity_updates[1].interaction.reset is True

def replace_interaction(ent, progress):
    from dataclasses import replace
    from src.core.state import InteractionComponent
    return replace(ent, interaction=InteractionComponent(progress=progress, target_node_id=100))

def test_strategic_bandwidth_leads():
    # Setup entity with max_leads = 2
    profile = CognitionProfile(max_leads=2, max_concerns=10)
    strat = StrategicComponent(profile=profile)
    ent = EntityState(id=1, kind="HERO", position=(0,0), strategic=strat)
    
    # Generate 5 leads
    leads = [LeadState(id=f"L{i}", kind="location", subject=f"S{i}") for i in range(5)]
    
    # Test bandwidth enforcement
    from src.systems.detour import DetourSuggestionSystem
    strat_upd = StrategicUpdate(leads_add_or_update=leads)
    refined = DetourSuggestionSystem.enforce_bandwidth(ent, 10)
    
    # Actually, we need to apply the leads first or pass them to enforce_bandwidth if it supported it
    # But current enforce_bandwidth checks existing leads in entity.strategic
    ent = replace_leads(ent, leads)
    refined = DetourSuggestionSystem.enforce_bandwidth(ent, 10)
    assert len(refined.leads_remove) == 3 # 5 - 2 = 3
def replace_leads(ent, leads):
    from dataclasses import replace
    new_strat = replace(ent.strategic, leads={l.id: l for l in leads})
    return replace(ent, strategic=new_strat)
