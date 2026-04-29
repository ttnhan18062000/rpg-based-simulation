import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, CombatComponent, InventoryComponent, SocialComponent, IdentityComponent, BiologicalComponent, LifecycleComponent, StrategicComponent
from src.core.strategic import ContractState, ContractKind, ContractStatus, ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus
from src.systems.party import PartyCoordinationSystem
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

def test_party_coordination_leadership_influence():
    # 1. Setup Leader
    leader = create_mock_entity(1)
    obj = ObjectiveState(id="obj_l1", kind="harvesting", target="node_101", status=ObjectiveStatus.ACTIVE)
    proj = ProjectState(
        id="proj_l1", 
        kind="harvesting", 
        status=ProjectStatus.ACTIVE, 
        objectives=[obj],
        active_objective_id=obj.id
    )
    new_strat = replace(leader.strategic, projects={proj.id: proj}, current_project_id=proj.id)
    leader = replace(leader, strategic=new_strat)
    
    # 2. Setup Member
    member = create_mock_entity(2)
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=2,
        status=ContractStatus.ACTIVE
    )
    new_member_strat = replace(member.strategic, contracts={contract.id: contract})
    member = replace(member, strategic=new_member_strat)
    
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
