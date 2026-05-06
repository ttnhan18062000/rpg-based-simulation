import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, CombatComponent, InventoryComponent, SocialComponent, IdentityComponent, BiologicalComponent, LifecycleComponent, StrategicComponent
from src.core.strategic import LeadState, LeadCertainty, ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.enums import EntityRole
from src.core.builder import V2EntityBuilder

def create_mock_entity(eid: int):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("hero")
        .active(True)
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction="player")
        .combat(hp=100, max_hp=100, atk=10, def_stat=5)
        .inventory(gold=10)
        .build())

def test_lead_failure_suppression():
    # Lead that just failed
    lead = LeadState(id="l1", kind="location", subject="forest", tested=True, test_outcome="FAILURE")
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .active(True)
        .location(0, 0)
        .strategic(leads={lead.id: lead})
        .build())
    
    state = AuthoritativeState(tick=100, seed=42)
    
    # Run evaluation
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    
    # Should contain suppression update
    assert len(update.leads_add_or_update) > 0
    updated_lead = update.leads_add_or_update[0]
    assert updated_lead.failure_count == 1
    assert updated_lead.suppression_until_tick == 100 + 500

def test_lead_exhaustion():
    # Lead that failed 2 times already
    lead = LeadState(id="l1", kind="location", subject="forest", tested=True, test_outcome="FAILURE", failure_count=2)
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .active(True)
        .location(0, 0)
        .strategic(leads={lead.id: lead})
        .build())
    
    state = AuthoritativeState(tick=100, seed=42)
    
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    
    # Should be EXHAUSTED after 3rd failure
    assert len(update.leads_add_or_update) > 0
    updated_lead = update.leads_add_or_update[0]
    assert updated_lead.failure_count == 3
    assert updated_lead.certainty == LeadCertainty.EXHAUSTED

def test_project_abandonment():
    # Project that failed 3 times
    proj = ProjectState(id="p1", kind="quest", status=ProjectStatus.ACTIVE, failure_count=3)
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .active(True)
        .location(0, 0)
        .strategic(projects={proj.id: proj})
        .current_project(proj.id)
        .build())
    
    state = AuthoritativeState(tick=100, seed=42)
    
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
    
    # Should be ABANDONED
    assert len(update.projects_add_or_update) > 0
    abandoned_proj = next(p for p in update.projects_add_or_update if p.id == "p1")
    assert abandoned_proj.status == ProjectStatus.ABANDONED
    # Should have frustration boredom (0.1 base + 0.5 penalty = 0.6)
    assert update.boredom_delta["quest"] == 0.6
