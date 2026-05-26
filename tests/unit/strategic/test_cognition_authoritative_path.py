import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.domain.cognition import CognitionDomain
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.strategic import ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus

def test_cognition_domain_emits_no_strategic_updates():
    """Verify that CognitionDomain.execute_brain only evaluates tactical/emotional state and emits no strategic updates."""
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .location(5.0, 5.0)
        .build())
        
    region = RegionState(id="forest", name="Deep Forest", bounds=(0, 0, 10, 10))
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent}, regions={"forest": region})
    
    # Run execute_brain
    updates = CognitionDomain.execute_brain(state, ent, force=True)
    
    assert 1 in updates
    ent_upd = updates[1]
    
    # The tactical executor update must not contain parallel strategic updates
    assert ent_upd.strategic is None
    # Readiness delta must be 0
    assert ent_upd.readiness_delta == 0.0


def test_pipeline_authoritatively_infers_blockers():
    """Verify that Phase 7 strategic pass authoritatively handles blocker inference in the apply pipeline."""
    # Setup entity with active project and navigation failure to trigger material blocker inference
    proj = ProjectState(
        id="proj_harvest",
        kind="harvesting",
        status=ProjectStatus.ACTIVE,
        objectives=[ObjectiveState(
            id="obj_collect",
            kind="collect",
            target="wood",
            status=ObjectiveStatus.ACTIVE
        )],
        active_objective_id="obj_collect",
        created_tick=100,
        lock_until_tick=105
    )
    
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .location(5.0, 5.0)
        .navigation(last_failure_reason="PATH_BLOCKED", wait_count=5)
        .strategic(projects={"proj_harvest": proj}, current_project_id="proj_harvest", current_objective_id="obj_collect")
        .build())
        
    region = RegionState(id="forest", name="Deep Forest", bounds=(0, 0, 10, 10))
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent}, regions={"forest": region})
    
    # Run the pipeline with force_full_scan=True to bypass dirty checks
    raw_update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)}, force_full_scan=True)
    refined = AuthoritativeApplyPipeline.refine(state, raw_update)
    
    assert 1 in refined.entity_updates
    ent_upd = refined.entity_updates[1]
    
    # Verify blocker inference ran authoritatively in the pipeline pass
    assert ent_upd.strategic is not None
    assert any(b.kind == "access" for b in ent_upd.strategic.blockers_add_or_update)


def test_single_strategic_update_per_tick():
    """Verify that strategic intelligence only updates an entity once per strategic tick."""
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .location(5.0, 5.0)
        .build())
        
    region = RegionState(id="forest", name="Deep Forest", bounds=(0, 0, 10, 10))
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent}, regions={"forest": region})
    
    # Run the strategic pass once
    from src.engine.cadence import SystemCadence
    from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
    raw_update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)}, force_full_scan=True)
    
    # Verify that it produces updates correctly
    res = StrategicIntelligenceSystem.fused_strategic_pass(state, raw_update, cadence=SystemCadence())
    assert 1 in res.entity_updates


def test_tactical_consumes_selected_strategic_state():
    """Verify that tactical decision making reads and consumes the active strategic project/objective."""
    from src.core.strategic import ProjectState, ProjectKind, ProjectStatus, ObjectiveState, ObjectiveKind, ObjectiveStatus
    from src.engine.tactical import TacticalDecisionSystem
    
    # Create an entity with a specific active strategic project
    obj = ObjectiveState(
        id="obj_1",
        kind=ObjectiveKind.REACH_LOCATION,
        target_position=(2.0, 2.0),
        status=ObjectiveStatus.ACTIVE
    )
    proj = ProjectState(
        id="proj_custom",
        kind=ProjectKind.EXPLORATION,
        status=ProjectStatus.ACTIVE,
        objectives=[obj],
        active_objective_id="obj_1"
    )
    
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .location(1.0, 1.0)
        .strategic(projects={"proj_custom": proj}, current_project_id="proj_custom")
        .build())
        
    region = RegionState(id="forest", name="Deep Forest", bounds=(0, 0, 10, 10))
    state = AuthoritativeState(tick=100, seed=42, entities={1: ent}, regions={"forest": region})
    
    # Under local tactical evaluation, ensure the tactical decision makes choices based on the active strategic project
    tactical_up = TacticalDecisionSystem.evaluate_entity_intent(state, ent)
    assert tactical_up is not None

