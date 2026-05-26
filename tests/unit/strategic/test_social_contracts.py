import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.systems.social_systems.contracts import ContractService
from src.systems.social_systems.appraisal import SocialAppraisalSystem

def test_accepted_contract_spawns_project_and_objective():
    """Verify that accepting recruitment/loan contracts automatically spawns strategic projects & objectives."""
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .build())
        
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        status=ContractStatus.OFFERED
    )
    
    # Add contract to entity state
    ent = V2EntityBuilder(1).kind("HERO").strategic(contracts={"c1": contract}).build()
    
    # Accept contract
    strat_up = ContractService.accept_contract(ent, "c1", tick=100)
    
    assert strat_up.current_project_id_set == "proj_contract_c1"
    assert len(strat_up.projects_add_or_update) == 1
    
    proj = strat_up.projects_add_or_update[0]
    assert proj.id == "proj_contract_c1"
    assert proj.kind == "combat"
    assert len(proj.objectives) == 1
    assert proj.objectives[0].id == "obj_recruit_c1"
    assert proj.objectives[0].target == "2"

def test_contract_failure_degrades_trust():
    """Verify that contract failure degrades trust/sentiment between entities."""
    ent = (V2EntityBuilder(1)
        .kind("HERO")
        .build())
        
    contract = ContractState(
        id="c2",
        kind=ContractKind.LOAN,
        source_id=1,
        target_id=2,
        status=ContractStatus.ACTIVE
    )
    
    ent = V2EntityBuilder(1).kind("HERO").strategic(contracts={"c2": contract}).build()
    
    # Resolve contract outcome as failed
    strat_up, social_ups = ContractService.resolve_contract_outcome(ent, "c2", success=False, tick=100)
    
    assert strat_up.contracts_add_or_update[0].status == ContractStatus.FAILED
    assert len(social_ups) == 2
    
    # First returned SocialUpdate is for entity passed in
    my_social = social_ups[0]
    assert len(my_social.bond_updates) == 1
    assert my_social.bond_updates[0].sentiment_delta == -0.2

def test_betrayal_history_blocks_contracts():
    """Verify that an entity's betrayal history blocks future contract acceptance."""
    # Recruiter has betrayal history, and candidate has low trust for recruiter
    candidate = (V2EntityBuilder(1)
        .kind("HERO")
        .social(betrayal_count=1, trust_history={2: 0.1})
        .build())
        
    contract = ContractState(
        id="c3",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        status=ContractStatus.OFFERED
    )
    
    region = RegionState(id="forest", name="Deep Forest", bounds=(0, 0, 10, 10))
    state = AuthoritativeState(tick=100, seed=42, entities={1: candidate}, regions={"forest": region})
    
    status, reason, _ = SocialAppraisalSystem.appraise_contract(candidate, contract, state)
    assert status == ContractStatus.CANCELLED
    assert reason.value == "betrayal_history"
