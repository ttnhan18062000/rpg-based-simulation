import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    CombatComponent, InventoryComponent, StrategicComponent, 
    BiologicalComponent, SocialComponent, NavigationComponent,
    LifecycleComponent, EntityRole, AttributeComponent, TaskComponent, InteractionComponent
)
from src.core.enums import Faction, EntityRole, ReasonCode
from src.core.strategic import (
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    BlockerState, LeadState, LeadCertainty, CognitionProfile
)
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.detour import DetourSuggestionSystem
from src.systems.belief import BeliefCycleSystem
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate, NavigationUpdate

def create_mock_hero(e_id, pos):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(e_id)
        .kind("actor")
        .position(pos[0], pos[1])
        .role(EntityRole.HERO)
        .faction(Faction.HERO_GUILD)
        .hp(100, max_hp=100)
        .alive(True)
        .readiness(100.0)
        .cognition(interruption_resistance=0.5, detour_breadth=3)
        .build())

@pytest.mark.strategic_loop
def test_end_to_end_strategic_detour_lifecycle():
    """
    Complete Phase 6 Lifecycle Test:
    1. Project starts (Harvest Wood).
    2. Navigation fails (Broken Bridge).
    3. Blocker inferred (access: Broken Bridge).
    4. Lead discovered (Rumor: Ford).
    5. Detour suggested & accepted.
    6. Detour executed & resolved.
    7. Original project resumed.
    """
    hero = create_mock_hero(1, (1.0, 1.0))
    # 1. Start Harvest Project
    obj_harvest = ObjectiveState(id="obj_harvest_50", kind="harvesting", target="50", status=ObjectiveStatus.ACTIVE)
    proj_harvest = ProjectState(
        id="proj_harvest_wood", kind="harvesting", status=ProjectStatus.ACTIVE,
        objectives=[obj_harvest], active_objective_id=obj_harvest.id, score=80.0
    )
    hero = replace(hero, strategic=replace(hero.strategic, 
        projects={proj_harvest.id: proj_harvest},
        current_project_id=proj_harvest.id,
        current_objective_id=obj_harvest.id
    ))
    
    # Target iron at (10,10)
    node_pos = (10.0, 10.0)
    from src.core.state import ResourceNodeState
    node = ResourceNodeState(id=50, kind="iron", position=node_pos, yields_item="iron", remaining_charges=5, max_charges=5, required_ticks=5)
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero}, resource_nodes={50: node})
    state.blocked_tiles.add((5, 5)) # Direct path
    state.blocked_tiles.add((4, 6)) # Sidestep 1
    state.blocked_tiles.add((4, 4)) # Sidestep 2
    
    # --- TICK 1: Movement Attempt ---
    # Hero wants to move towards (10,10)
    # We put the blocker at (5,5) and hero at (4,5)
    hero = replace(hero, navigation=replace(hero.navigation, position=(4.0, 5.0)))
    state = replace(state, entities={1: hero})
    
    # Propose movement to (5,5) or beyond
    # MovementSystem will try to step to (5,5) and fail
    task_up = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "MOVE", "target_position": node_pos})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task_up, navigation=NavigationUpdate(target_set=node_pos))})
    
    # AuthoritativeApplyPipeline._route_movement_intent uses blocked_tiles
    update_tick1 = AuthoritativeApplyPipeline._route_movement_intent(state, update)
    hero_upd1 = update_tick1.entity_updates[1]
    
    assert hero_upd1.navigation.failure_reason == ReasonCode.PATH_NOT_FOUND
    assert hero_upd1.strategic is not None
    assert len(hero_upd1.strategic.blockers_add_or_update) > 0
    
    blocker = hero_upd1.strategic.blockers_add_or_update[0]
    assert blocker.kind == "access"
    
    # --- TICK 2: Information Discovery ---
    # Apply the blocker to hero state
    hero = replace(hero, strategic=replace(hero.strategic, blockers={blocker.id: blocker}))
    
    # Injected rumor about alternate route "Ford"
    # Subject matches the failure reason
    rumor_upd = BeliefCycleSystem.process_rumor(hero, rumor_subject=blocker.subject, rumor_detail="(2.0, 2.0)", source_entity_id=99, current_tick=2)
    hero = replace(hero, strategic=replace(hero.strategic, leads={l.id: l for l in rumor_upd.leads_add_or_update}))
    
    # --- TICK 3: Detour Suggestion ---
    detours = DetourSuggestionSystem.suggest_detours(hero, current_tick=3)
    assert len(detours) > 0
    best = detours[0]
    assert best.objective_kind == "reach_location"
    
    # --- TICK 4: Switch to Detour Project ---
    strat_upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)
    print(f"DEBUG: strat_upd={strat_upd}")
    if not strat_upd.current_project_id_set:
        print("DEBUG: No project switch suggested")
        # Check scores manually
        detours = DetourSuggestionSystem.suggest_detours(hero, current_tick=4)
        if detours:
            best = detours[0]
            print(f"DEBUG: Best detour score={best.score}, objective={best.objective_kind}")
            profile = hero.strategic.profile
            retention_margin = profile.interruption_resistance * 30
            effective_current_score = proj_harvest.score + retention_margin
            print(f"DEBUG: Candidate total score={best.score + 50.0}, Current effective={effective_current_score}")

    assert strat_upd.current_project_id_set.startswith("proj_detour")
    
    # Check suspension of harvesting
    suspended = next(p for p in strat_upd.projects_add_or_update if p.id == proj_harvest.id)
    assert suspended.status == ProjectStatus.SUSPENDED
    
    # Apply detour project
    new_detour_proj = next(p for p in strat_upd.projects_add_or_update if p.id == strat_upd.current_project_id_set)
    hero = replace(hero, strategic=replace(hero.strategic, 
        projects={proj_harvest.id: suspended, new_detour_proj.id: new_detour_proj},
        current_project_id=new_detour_proj.id,
        current_objective_id=new_detour_proj.active_objective_id
    ))
    
    # --- TICK 5-10: Execute Detour ---
    # Simulation: Hero reaches (2,2)
    hero = replace(hero, navigation=replace(hero.navigation, position=(2.0, 2.0)))
    state = replace(state, entities={1: hero})
    
    # --- TICK 11: Resolution ---
    # Hero is at (2,2). evaluate_strategic_intent should complete the detour.
    strat_upd_res = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)
    assert strat_upd_res.current_project_id_set == "" # Project completed
    assert any(p.status == ProjectStatus.COMPLETED for p in strat_upd_res.projects_add_or_update)
    
    # Apply completion
    comp_detour = next(p for p in strat_upd_res.projects_add_or_update if p.kind == "detour")
    hero = replace(hero, strategic=replace(hero.strategic,
        projects={proj_harvest.id: suspended, comp_detour.id: comp_detour},
        current_project_id="",
        current_objective_id=""
    ))
    
    # --- TICK 12: Resumption ---
    # Now that detour is COMPLETED, evaluate_strategic_intent should resolve blocker and resume harvesting.
    strat_upd_resume = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero, force=True)
    assert strat_upd_resume.current_project_id_set == proj_harvest.id
    assert any(b.id == blocker.id and b.resolved for b in strat_upd_resume.blockers_add_or_update)
    
    # Final check: Harvesting resumed
    assert strat_upd_resume.current_objective_id_set == obj_harvest.id
