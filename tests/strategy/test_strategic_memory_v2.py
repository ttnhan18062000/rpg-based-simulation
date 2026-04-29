import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, CombatComponent, InventoryComponent, SocialComponent, IdentityComponent, BiologicalComponent, LifecycleComponent, StrategicComponent
from src.core.strategic import LeadState, LeadCertainty, ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.enums import EntityRole

def create_mock_entity(eid: int):
    return EntityState(
        id=eid,
        kind="hero",
        active=True,
        position=(0, 0),
        identity=IdentityComponent(role=EntityRole.HERO, faction="player"),
        combat=CombatComponent(hp=100, max_hp=100, atk=10, def_stat=5, alive=True),
        inventory=InventoryComponent(gold=10),
        social=SocialComponent(),
        biological=BiologicalComponent(),
        lifecycle=LifecycleComponent(),
        strategic=StrategicComponent()
    )

def test_lead_failure_suppression():
    entity = create_mock_entity(1)
    # Lead that just failed
    lead = LeadState(id="l1", kind="location", subject="forest", tested=True, test_outcome="FAILURE")
    new_strat = replace(entity.strategic, leads={lead.id: lead})
    entity = replace(entity, strategic=new_strat)
    
    state = AuthoritativeState(tick=100, seed=42)
    
    # Run evaluation
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    
    # Should contain suppression update
    assert len(update.leads_add_or_update) > 0
    updated_lead = update.leads_add_or_update[0]
    assert updated_lead.failure_count == 1
    assert updated_lead.suppression_until_tick == 100 + 500

def test_lead_exhaustion():
    entity = create_mock_entity(1)
    # Lead that failed 2 times already
    lead = LeadState(id="l1", kind="location", subject="forest", tested=True, test_outcome="FAILURE", failure_count=2)
    new_strat = replace(entity.strategic, leads={lead.id: lead})
    entity = replace(entity, strategic=new_strat)
    
    state = AuthoritativeState(tick=100, seed=42)
    
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    
    # Should be EXHAUSTED after 3rd failure
    assert len(update.leads_add_or_update) > 0
    updated_lead = update.leads_add_or_update[0]
    assert updated_lead.failure_count == 3
    assert updated_lead.certainty == LeadCertainty.EXHAUSTED

def test_project_abandonment():
    entity = create_mock_entity(1)
    # Project that failed 3 times
    proj = ProjectState(id="p1", kind="quest", status=ProjectStatus.ACTIVE, failure_count=3)
    new_strat = replace(entity.strategic, projects={proj.id: proj}, current_project_id=proj.id)
    entity = replace(entity, strategic=new_strat)
    
    state = AuthoritativeState(tick=100, seed=42)
    
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    
    # Should be ABANDONED
    assert len(update.projects_add_or_update) > 0
    abandoned_proj = next(p for p in update.projects_add_or_update if p.id == "p1")
    assert abandoned_proj.status == ProjectStatus.ABANDONED
    # Should have frustration boredom (0.1 base + 0.5 penalty = 0.6)
    assert update.boredom_delta["quest"] == 0.6
