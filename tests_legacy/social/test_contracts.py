import pytest
from src_legacy.core.state import AuthoritativeState
from src_legacy.core.updates import EntityUpdate, StrategicUpdate, StateUpdate
from src_legacy.engine.apply import ApplyPath
from src_legacy.core.builder import V2EntityBuilder
from src_legacy.social.contracts import ContractService
from src_legacy.core.strategic import ContractKind

def test_contract_addition():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Create recruitment contract
    contract = ContractService.create_recruitment_contract(
        contract_id="rec_1_99",
        source_id=1,
        target_id=99
    )
    
    update = EntityUpdate(
        entity_id=1,
        strategic=StrategicUpdate(contracts_add_or_update=[contract])
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    contracts = new_state.entities[1].strategic.contracts
    
    assert "rec_1_99" in contracts
    assert contracts["rec_1_99"].kind == ContractKind.RECRUITMENT
    assert contracts["rec_1_99"].terms["daily_pay"] == 10

def test_contract_removal():
    # Initial state with a contract
    contract = ContractService.create_recruitment_contract("c1", 1, 99)
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    # Manual injection for test setup
    from dataclasses import replace
    entity = replace(entity, strategic=replace(entity.strategic, contracts={"c1": contract}))
    
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Remove contract c1
    update = EntityUpdate(
        entity_id=1,
        strategic=StrategicUpdate(contracts_remove=["c1"])
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    contracts = new_state.entities[1].strategic.contracts
    
    assert "c1" not in contracts

def test_loan_contract():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    loan = ContractService.create_loan_contract("loan_1", 1, 2, amount=100)
    
    update = EntityUpdate(
        entity_id=1,
        strategic=StrategicUpdate(contracts_add_or_update=[loan])
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    contracts = new_state.entities[1].strategic.contracts
    
    assert contracts["loan_1"].terms["total_due"] == 110
