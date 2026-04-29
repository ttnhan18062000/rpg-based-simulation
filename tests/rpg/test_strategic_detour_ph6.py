import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState
from src.core.strategic import (
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    BlockerState, LeadState, LeadCertainty
)
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.updates import StateUpdate

def create_mock_entity(eid: int):
    from src.core.state import CombatComponent, InventoryComponent, SocialComponent, IdentityComponent, BiologicalComponent, LifecycleComponent, StrategicComponent
    from src.core.enums import EntityRole
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

def test_strategic_detour_creation_and_resumption():
    # 1. Setup Entity with Blocker and Lead
    entity = create_mock_entity(1)
    
    # Existing project (harvesting)
    harvest_proj = ProjectState(
        id="proj_harvest",
        kind="harvesting",
        status=ProjectStatus.ACTIVE,
        score=40.0
    )
    
    # Blocker for wood
    blocker = BlockerState(id="blocker_mat_wood", kind="material", subject="wood")
    
    # Lead for wood
    lead = LeadState(
        id="lead_wood",
        kind="location",
        subject="wood",
        detail="(10.0, 10.0)",
        certainty=LeadCertainty.PRECISE
    )
    
    entity = replace(entity, strategic=replace(entity.strategic,
        projects={"proj_harvest": harvest_proj},
        current_project_id="proj_harvest",
        blockers={"blocker_mat_wood": blocker},
        leads={"lead_wood": lead}
    ))
    
    state = AuthoritativeState(tick=100, seed=42)
    
    # 2. evaluate_strategic_intent should suggest a detour
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    
    assert update.current_project_id_set is not None
    assert "proj_detour" in update.current_project_id_set
    
    # Verify harvest project is suspended
    harvest_up = next((p for p in update.projects_add_or_update if p.id == "proj_harvest"), None)
    assert harvest_up is not None
    assert harvest_up.status == ProjectStatus.SUSPENDED
    
    # 3. Simulate Detour Completion
    # We'll create a new state where the detour is completed
    detour_proj = next((p for p in update.projects_add_or_update if p.kind == "detour"), None)
    detour_obj = replace(detour_proj.objectives[0], status=ObjectiveStatus.RESOLVED)
    detour_proj = replace(detour_proj, status=ProjectStatus.COMPLETED, objectives=[detour_obj])
    
    entity = replace(entity, strategic=replace(entity.strategic,
        projects={
            "proj_harvest": harvest_up,
            detour_proj.id: detour_proj
        },
        current_project_id=detour_proj.id
    ))
    
    # 4. evaluate_strategic_intent should resume harvest project
    update_resume = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    
    assert update_resume.current_project_id_set == "proj_harvest"
    harvest_resumed = next((p for p in update_resume.projects_add_or_update if p.id == "proj_harvest"), None)
    assert harvest_resumed.status == ProjectStatus.ACTIVE
    
    # Verify blocker is marked as resolved (Phase 6 rule)
    resolved_blocker = next((b for b in update_resume.blockers_add_or_update if b.id == "blocker_mat_wood"), None)
    assert resolved_blocker.resolved == True
