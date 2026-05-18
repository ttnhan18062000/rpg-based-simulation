
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, NavigationComponent, CombatComponent, StrategicComponent, IdentityComponent, InteractionComponent
from src.core.updates import StateUpdate, EntityUpdate
from src.core.strategic import ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus, LeadState, LeadCertainty, BlockerState
from src.engine.domain_logic import SimulationDomainLogic
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.builder import V2EntityBuilder

def create_mock_entity(id, pos=(0,0), project=None):
    builder = (V2EntityBuilder(id)
               .kind("ACTOR")
               .location(*pos)
               .combat(hp=100, atk=10)
               .lifecycle(active=True))
    
    if project:
        builder = builder.strategic(
            projects={project.id: project},
            current_project_id=project.id
        )
    
    return builder.build()

def test_blocker_inference_and_detour():
    # 1. Setup project: Harvest Wood at (10,10)
    obj = ObjectiveState(id="obj1", kind="reach_location", target="10", status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="proj1", kind="harvesting", status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id="obj1")
    
    entity = create_mock_entity(1, pos=(10,10), project=project)
    
    # 2. Simulate Interaction Failure (Empty Node)
    # Entity is at the node, trying to interact
    entity = replace(entity, 
                     task=replace(entity.task, work_kind="ENTITY_ACT", payload={"action": "INTERACT", "target_id": 10}))
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    
    # 3. Setup lead for "resource"
    lead = LeadState(id="lead1", kind="location", subject="(5, 5)", detail="Alternative resource source", certainty=LeadCertainty.PRECISE)
    entity = replace(entity, strategic=replace(entity.strategic, leads={"lead1": lead}))
    
    # 4. Execute Brain
    updates = SimulationDomainLogic.execute_brain(state, entity, force=True)
    ent_up = updates[1]
    
    # Verify blocker was inferred
    assert any(b.kind == "material" and b.subject == "resource" for b in ent_up.strategic.blockers_add_or_update)
    
    # Verify detour project was suggested and switched to
    assert ent_up.strategic.current_project_id_set.startswith("proj_detour_")
    assert ent_up.strategic.current_objective_id_set.startswith("detour_blocker_node_10")

def test_detour_completion_and_resumption():
    # 1. Setup: Suspended parent + Active detour
    parent = ProjectState(id="parent", kind="harvesting", status=ProjectStatus.SUSPENDED)
    detour_obj = ObjectiveState(id="d_obj", kind="reach_location", target="(5, 5)", status=ObjectiveStatus.ACTIVE)
    detour = ProjectState(id="detour", kind="detour", status=ProjectStatus.ACTIVE, objectives=[detour_obj], active_objective_id="d_obj")
    
    entity = create_mock_entity(1, pos=(0,0))
    entity = replace(entity, strategic=replace(entity.strategic, 
                                               projects={"parent": parent, "detour": detour},
                                               current_project_id="detour",
                                               current_objective_id="d_obj"))
    
    # 2. Mark detour as COMPLETED (simulating success)
    detour_completed = replace(detour, status=ProjectStatus.COMPLETED)
    entity = replace(entity, strategic=replace(entity.strategic, projects={"parent": parent, "detour": detour_completed}))
    
    state = AuthoritativeState(entities={1: entity}, tick=100, seed=1)
    
    # 3. Execute Brain - should resume parent
    updates = SimulationDomainLogic.execute_brain(state, entity, force=True)
    ent_up = updates[1]
    
    assert ent_up.strategic.current_project_id_set == "parent"
    assert any(p.id == "parent" and p.status == ProjectStatus.ACTIVE for p in ent_up.strategic.projects_add_or_update)

def test_access_blocker_resolution():
    # 1. Setup: Project blocked by ACCESS
    blocker = BlockerState(id="b_acc", kind="access", subject="(10, 10)", severity=0.8)
    parent = ProjectState(id="parent", kind="harvesting", status=ProjectStatus.ACTIVE)
    
    entity = create_mock_entity(1, pos=(0,0))
    entity = replace(entity, strategic=replace(entity.strategic, 
                                               projects={"parent": parent},
                                               blockers={"b_acc": blocker},
                                               current_project_id="parent"))
    
    # 2. Reach (10,10) - should resolve blocker
    entity = replace(entity, navigation=replace(entity.navigation, position=(10, 10)))
    state = AuthoritativeState(entities={1: entity}, tick=100, seed=1)
    
    # 3. Execute Brain - resolve_blockers is called in domain_logic?
    # Wait, SimulationDomainLogic.execute_brain doesn't call resolve_blockers yet!
    # The Kernel calls it in Phase 4 (Resolution).
    
    # Let's check StrategicIntelligenceSystem.resolve_blockers directly
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)})
    resolved_up = StrategicIntelligenceSystem.resolve_blockers(state, update)
    
    ent_up = resolved_up.entity_updates[1]
    assert any(b.id == "b_acc" and b.resolved for b in ent_up.strategic.blockers_add_or_update)
