import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, StrategicComponent
from src.core.strategic import ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus, BlockerState, ProjectKind
from src.core.updates import StateUpdate, EntityUpdate
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.builder import V2EntityBuilder

def test_goal_hysteresis_and_detour_resumption():
    # Observer at (0, 0)
    # We need to set up the strategic component properly. 
    # V2EntityBuilder doesn't have a direct strategic() method yet, 
    # but we can build it and then replace the component if needed, 
    # or add a method to the builder.
    
    # Actually, let's use the builder's with_property or similar if we can't do it directly.
    # But for a full strategic setup, it's easier to build and then replace.
    
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0.0, 0.0)
              .build())

    # 1. Active Main Project: Reach (100, 100)
    obj_main = ObjectiveState(id="obj_main", kind="reach_location", target="(100.0, 100.0)", status=ObjectiveStatus.ACTIVE)
    proj_main = ProjectState(
        id="proj_main", kind=ProjectKind.EXPLORATION, status=ProjectStatus.ACTIVE,
        objectives=[obj_main], active_objective_id="obj_main", score=50.0,
        lock_until_tick=100
    )
    
    blocker = BlockerState(id="blocker_gold", kind="material", subject="gold", severity=1.0)
    from src.core.strategic import LeadState, LeadCertainty
    lead = LeadState(id="lead_gold", kind="material", subject="gold", certainty=LeadCertainty.PRECISE)
    
    strat = StrategicComponent(
        projects={"proj_main": proj_main},
        current_project_id="proj_main",
        current_objective_id="obj_main",
        blockers={"blocker_gold": blocker},
        leads={"lead_gold": lead}
    )
    
    # Authoritative replacement
    entity = replace(entity, strategic=strat)
    
    # We need (tick + entity_id) % 10 == 0
    # 109 + 1 = 110
    state = AuthoritativeState(tick=109, seed=42, entities={1: entity})
    
    # Tick 109: Evaluate intent
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    
    assert update.current_project_id_set is not None
    assert update.current_project_id_set.startswith("proj_detour")
    
    proj_updates = {p.id: p for p in update.projects_add_or_update}
    assert proj_updates["proj_main"].status == ProjectStatus.SUSPENDED
    
    # --- MOCK COMPLETION OF DETOUR ---
    detour_proj = proj_updates[update.current_project_id_set]
    entity = replace(entity, strategic=replace(entity.strategic,
        projects={**entity.strategic.projects, **proj_updates},
        current_project_id=detour_proj.id,
        current_objective_id=detour_proj.active_objective_id
    ))
    state = replace(state, entities={1: entity})
    
    # Mark detour objective as RESOLVED and project as COMPLETED
    resolved_obj = replace(detour_proj.objectives[0], status=ObjectiveStatus.RESOLVED)
    completed_detour = replace(detour_proj, objectives=[resolved_obj], status=ProjectStatus.COMPLETED)
    
    entity = replace(entity, strategic=replace(entity.strategic,
        projects={**entity.strategic.projects, completed_detour.id: completed_detour}
    ))
    # Still need (tick + 1) % 10 == 0
    # 119 + 1 = 120
    state = AuthoritativeState(tick=119, seed=42, entities={1: entity})
    
    # Tick 119: Evaluate intent again. Should resume proj_main.
    update_resume = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity)
    
    assert update_resume.current_project_id_set == "proj_main"
    assert update_resume.current_objective_id_set == "obj_main"
    
    proj_updates_resume = {p.id: p for p in update_resume.projects_add_or_update}
    assert proj_updates_resume["proj_main"].status == ProjectStatus.ACTIVE
    
    print("\nSuccessfully demonstrated Detour switch and Hysteresis resumption.")
