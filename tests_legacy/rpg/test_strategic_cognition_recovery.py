import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, StrategicComponent, NavigationComponent, ResourceNodeState
from src_legacy.core.strategic import LeadCertainty, ProjectState, ObjectiveState, ProjectStatus, ObjectiveStatus, CognitionProfile, BlockerState, LeadState
from src_legacy.systems.strategic import StrategicIntelligenceSystem
from src_legacy.core.updates import StateUpdate, EntityUpdate

def test_lead_failure_and_suppression():
    """
    Law: Reached leads that don't resolve blockers must be suppressed.
    """
    # 1. Setup: Entity with blocker and lead
    blocker = BlockerState(id="blocker_mat_iron", kind="material", subject="iron")
    lead = LeadState(
        id="lead_iron_1", kind="location", subject="iron", 
        target_pos=(5, 5), certainty=LeadCertainty.VAGUE
    )
    obj = ObjectiveState(
        id="reach_iron_1", kind="reach_location", target="101", # Node 101 at (5,5)
        status=ObjectiveStatus.ACTIVE, lead_id="lead_iron_1"
    )
    proj = ProjectState(
        id="proj_iron", kind="detour", status=ProjectStatus.ACTIVE,
        objectives=[obj], active_objective_id="reach_iron_1"
    )
    
    entity = EntityState(
        id=1, kind="HERO", position=(0,0),
        strategic=StrategicComponent(
            blockers={"blocker_mat_iron": blocker},
            leads={"lead_iron_1": lead},
            projects={"proj_iron": proj},
            current_project_id="proj_iron",
            current_objective_id="reach_iron_1",
            profile=CognitionProfile(max_leads=5)
        ),
        navigation=NavigationComponent(target=(5,5))
    )
    
    # Node at (5,5)
    node = ResourceNodeState(id=101, kind="IRON_VEIN", position=(5,5), yields_item="iron", remaining_charges=1, max_charges=1, required_ticks=5)
    
    state = AuthoritativeState(tick=10, seed=42, entities={1: entity}, resource_nodes={101: node})
    
    # 2. Simulate reaching the target but NO iron added to inventory
    # (So blocker remains unresolved)
    upd = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, new_position=(5,5))
    })
    
    # Run validate_leads
    upd_validated = StrategicIntelligenceSystem.validate_leads(state, upd)
    
    # Verify lead marked as failed
    ent_upd = upd_validated.entity_updates[1]
    assert ent_upd.strategic is not None
    failed_lead = next(l for l in ent_upd.strategic.leads_add_or_update if l.id == "lead_iron_1")
    assert failed_lead.tested is True
    assert failed_lead.test_outcome == 'FAILURE'
    
    # 3. Simulate next tick's evaluation (brain)
    # Apply the update to get a new entity state
    from src_legacy.engine.apply import ApplyPath
    state_after = ApplyPath.apply_generation(state, upd_validated)
    entity_after = state_after.entities[1]
    
    # Run evaluate_strategic_intent
    strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state_after, entity_after)
    
    # Verify lead is suppressed (marked EXHAUSTED)
    suppressed_lead = next(l for l in strat_up.leads_add_or_update if l.id == "lead_iron_1")
    assert suppressed_lead.certainty == LeadCertainty.EXHAUSTED
    
    # 4. Verify detour suggestion ignores it
    # Apply suppression
    entity_final = replace(entity_after, strategic=replace(entity_after.strategic, 
        leads={**entity_after.strategic.leads, "lead_iron_1": suppressed_lead}
    ))
    
    from src_legacy.systems.detour import DetourSuggestionSystem
    suggestions = DetourSuggestionSystem.suggest_detours(entity_final, 11)
    assert not any(s.lead_id == "lead_iron_1" for s in suggestions)

def replace(obj, **kwargs):
    from dataclasses import replace as dr
    return dr(obj, **kwargs)
