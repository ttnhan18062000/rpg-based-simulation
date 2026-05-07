import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, CombatComponent, InventoryComponent, SocialComponent, IdentityComponent, BiologicalComponent, LifecycleComponent, StrategicComponent
from src.core.strategic import ContractState, ContractKind, ContractStatus, ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus
from src.systems.party import PartyCoordinationSystem
from src.core.enums import EntityRole, Faction

def create_mock_entity(eid: int):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=10)
        .build())

def test_party_coordination_leadership_influence():
    # 1. Setup Leader
    from src.core.builder import V2EntityBuilder
    obj = ObjectiveState(id="obj_l1", kind="harvesting", target="node_101", status=ObjectiveStatus.ACTIVE)
    proj = ProjectState(
        id="proj_l1", 
        kind="harvesting", 
        status=ProjectStatus.ACTIVE, 
        objectives=[obj],
        active_objective_id=obj.id
    )
    leader = (V2EntityBuilder(1)
        .kind("hero")
        .strategic(projects={"proj_l1": proj})
        .build())
    # current_project_id needs to be set manually if builder doesn't support it yet
    leader = replace(leader, strategic=replace(leader.strategic, current_project_id=proj.id))
    
    # 2. Setup Member
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=2,
        status=ContractStatus.ACTIVE
    )
    member = (V2EntityBuilder(2)
        .kind("hero")
        .strategic(contracts={"c1": contract})
        .build())
    
    state = AuthoritativeState(tick=100, seed=42)
    state.entities[1] = leader
    state.entities[2] = member
    
    # 3. Apply influence
    scores = []
    influenced_scores = PartyCoordinationSystem.apply_leadership_influence(member, state, scores)
    
    # 4. Verify injection
    assert len(influenced_scores) == 1
    party_goal = influenced_scores[0]
    assert party_goal.kind == "harvesting"
    assert party_goal.target_id == "node_101"
    assert party_goal.utility >= 25.0
    assert party_goal.metadata["party_sync"] is True
    assert party_goal.metadata["leader_id"] == 1

def test_party_coordination_no_contract():
    member = create_mock_entity(2)
    state = AuthoritativeState(tick=100, seed=42)
    
    scores = []
    influenced_scores = PartyCoordinationSystem.apply_leadership_influence(member, state, scores)
    assert len(influenced_scores) == 0
