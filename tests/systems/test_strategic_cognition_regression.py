import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    CombatComponent, InventoryComponent, StrategicComponent, 
    BiologicalComponent, SocialComponent, NavigationComponent,
    LifecycleComponent, EntityRole
)
from src.core.strategic import (
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    BlockerState, LeadState, LeadCertainty, CognitionProfile
)
from src.engine.domain_logic import SimulationDomainLogic
from src.systems.strategic import StrategicIntelligenceSystem

def create_mock_entity(e_id, pos, faction=1, role=EntityRole.HERO):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(e_id)
        .kind("actor")
        .location(pos[0], pos[1])
        .identity(role=role)
        .identity(faction=faction)
        .combat(hp=100, max_hp=100)
        .combat(alive=True)
        .combat(readiness=100.0)
        .cognition(interruption_resistance=0.5, detour_breadth=3)
        .build())

def test_blocker_inference_on_failure():
    """Verify that a failed attack generates a blocker."""
    hero = create_mock_entity(1, (1.0, 1.0))
    # Target out of range
    monster = create_mock_entity(2, (10.0, 10.0), faction=2)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster})
    
    # We need to simulate the pipeline or call domain_logic then manually check if pipeline would have added blockers
    # Since I added blockers in AuthoritativeApplyPipeline, I should use a helper or test the pipeline
    from src.engine.pipeline import AuthoritativeApplyPipeline
    from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
    
    # Propose an ATTACK task
    task_up = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task_up)})
    
    refined_update = AuthoritativeApplyPipeline._route_combat_intent(state, update)
    hero_upd = refined_update.entity_updates[1]
    
    assert hero_upd.strategic is not None
    assert any(b.kind == "access" for b in hero_upd.strategic.blockers_add_or_update)
    assert any("OUT_OF_RANGE" in b.id for b in hero_upd.strategic.blockers_add_or_update)

def test_detour_suggestion_logic():
    """Verify that a blocker + lead triggers a detour project."""
    hero = create_mock_entity(1, (1.0, 1.0))
    # Add a material blocker
    blocker = BlockerState(id="blocker_mat_iron", kind="material", subject="iron", severity=1.0)
    # Add a location lead for iron
    lead = LeadState(id="lead_mine", kind="location", subject="iron", detail="mine_at_10_10", certainty=LeadCertainty.PRECISE)
    
    hero = replace(hero, strategic=replace(hero.strategic, 
        blockers={"blocker_mat_iron": blocker},
        leads={"lead_mine": lead},
        # Current project is crafting
        projects={"proj_craft": ProjectState(id="proj_craft", kind="crafting", status=ProjectStatus.ACTIVE, score=40.0)},
        current_project_id="proj_craft"
    ))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero})
    
    strat_up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)
    
    assert strat_up.current_project_id_set.startswith("proj_detour")
    assert strat_up.current_objective_id_set.startswith("detour_blocker_mat_iron")
    
    # Check that crafting is suspended
    suspended = next(p for p in strat_up.projects_add_or_update if p.id == "proj_craft")
    assert suspended.status == ProjectStatus.SUSPENDED

def test_blocker_resolution_on_pickup():
    """Verify that picking up a blocked material resolves the blocker."""
    hero = create_mock_entity(1, (1.0, 1.0))
    blocker = BlockerState(id="blocker_mat_iron", kind="material", subject="iron", severity=1.0)
    hero = replace(hero, strategic=replace(hero.strategic, blockers={"blocker_mat_iron": blocker}))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero})
    
    # Propose picking up iron
    from src.core.updates import InventoryUpdate, ItemStack, StateUpdate, StrategicUpdate, EntityUpdate
    inv_up = InventoryUpdate(items_add=[ItemStack(item_id="iron", quantity=1)])
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, inventory=inv_up)})
    
    resolved_update = StrategicIntelligenceSystem.resolve_blockers(state, update)
    hero_upd = resolved_update.entity_updates[1]
    
    assert "blocker_mat_iron" in hero_upd.strategic.blockers_remove
