"""
Contract lifecycle and social evaluation tests.
- RPG-0054: social_contracts_explicit
- RPG-0055: social_contract_consequences
- RPG-0059: social_recruitment_evaluation
"""

import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, SocialComponent, SocialBond
from src.core.builder import V2EntityBuilder
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.systems.social_systems.appraisal import SocialAppraisalSystem
from src.systems.social_systems.contracts import ContractService

def create_mock_entity(id, gold=10, sentiment=0.0):
    from src.core.builder import V2EntityBuilder
    from src.core.state import SocialBond
    return (V2EntityBuilder(id)
        .kind("ACTOR")
        .location(0, 0)
        .inventory(gold=gold)
        .social(bonds={99: SocialBond(target_id=99, sentiment=sentiment, familiarity=0.5)})
        .combat(alive=True)
        .build())

def test_contract_appraisal_trust():
    # Scenario: Trusted friend offers a low-pay recruitment
    friend = create_mock_entity(1, sentiment=0.9)
    contract = ContractService.create_recruitment_contract("c1", 99, 1, daily_pay=6, tick=100) # Pay 6 to ensure acceptance with trust
    
    state = AuthoritativeState(entities={1: friend}, tick=100, seed=1)
    
    from src.core.enums import ReasonCode
    status, reason, _ = SocialAppraisalSystem.appraise_contract(friend, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.LOYALTY_ACCEPTANCE

def test_contract_appraisal_greed():
    # Scenario: Desperate for gold, accepts high pay recruitment from stranger
    desperate = create_mock_entity(1, gold=0, sentiment=0.0)
    contract = ContractService.create_recruitment_contract("c2", 99, 1, daily_pay=20, tick=100)
    
    state = AuthoritativeState(entities={1: desperate}, tick=100, seed=1)
    
    from src.core.enums import ReasonCode
    status, reason, _ = SocialAppraisalSystem.appraise_contract(desperate, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.FAIR_COMPENSATION

def test_contract_appraisal_rejection():
    # Scenario: Low trust stranger offers low pay
    enemy = create_mock_entity(1, sentiment=-0.9)
    contract = ContractService.create_recruitment_contract("c3", 99, 1, daily_pay=5, tick=100)
    
    state = AuthoritativeState(entities={1: enemy}, tick=100, seed=1)
    
    from src.core.enums import ReasonCode
    status, reason, _ = SocialAppraisalSystem.appraise_contract(enemy, contract, state)
    assert status == ContractStatus.CANCELLED
    assert reason == ReasonCode.TOTAL_DISTRUST

def test_contract_lifecycle_acceptance():
    contract = ContractService.create_recruitment_contract("c4", 99, 1, tick=100)
    
    # Accept
    entity = create_mock_entity(1)
    # The entity must have the contract in its strategic component to accept it
    entity = (V2EntityBuilder(1)
        .kind("ACTOR")
        .location(0, 0)
        .strategic(contracts={contract.id: contract})
        .build())
    
    update = ContractService.accept_contract(entity, contract.id, tick=100)
    assert len(update.contracts_add_or_update) == 1
    new_contract = update.contracts_add_or_update[0]
    assert new_contract.status == ContractStatus.ACTIVE
    assert new_contract.expiry_tick == 200 # 100 + 100 duration

def test_accept_contract_no_longer_sets_current_project_id_directly():
    """
    TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER AC1 -- the single highest-value regression guard
    for this ticket's core behavior change. accept_contract() must no longer build any
    ProjectState/ObjectiveState or set current_project_id_set directly: project materialization
    now runs exclusively through SocialContractGoalScorer + evaluate_strategic_intent()'s
    SOCIAL_CONTRACT branch. Asserting `projects_add_or_update == []` (not just
    `current_project_id_set is None`) closes the Design Decision #7 duplicate-project/bandwidth
    hazard -- a future edit that re-adds any ProjectState construction to accept_contract() while
    leaving current_project_id_set alone would otherwise go undetected here.
    """
    contract = ContractService.create_recruitment_contract("c6", 99, 1, tick=100)
    entity = (V2EntityBuilder(1)
        .kind("ACTOR")
        .location(0, 0)
        .strategic(contracts={contract.id: contract})
        .build())

    update = ContractService.accept_contract(entity, contract.id, tick=100)

    assert update.current_project_id_set is None
    assert update.projects_add_or_update == []
    assert update.contracts_add_or_update[0].status == ContractStatus.ACTIVE


def test_contract_lifecycle_resolution():
    contract = ContractService.create_recruitment_contract("c5", 99, 1, tick=100)
    contract = replace(contract, status=ContractStatus.ACTIVE)
    
    # Create entity that owns the contract
    entity = V2EntityBuilder(1).kind("ACTOR").location(0, 0).strategic(contracts={contract.id: contract}).build()
    
    # Success
    s_upd, b_upds = ContractService.resolve_contract_outcome(entity, contract.id, success=True)
    assert s_upd.contracts_add_or_update[0].status == ContractStatus.FULFILLED
    assert b_upds[0].bond_updates[0].sentiment_delta == 0.2
    
    # Betrayal
    s_upd, b_upds = ContractService.resolve_contract_outcome(entity, contract.id, success=False, betrayal=True, betrayer_id=99)
    assert s_upd.contracts_add_or_update[0].status == ContractStatus.BETRAYED
    assert b_upds[0].bond_updates[0].sentiment_delta == -1.0


def test_contract_betrayal_produces_clan_reputation_clan_update():
    """Idea 54/M5 (SOC-268): a contract betrayal also produces a ClanUpdate
    degrading the betrayer's clan's clan_reputation, verified through
    ApplyPath. NOT wired to any live pipeline phase today --
    process_active_contracts() never passes betrayal=True/betrayer_id (a
    pre-existing gap, disclosed but not fixed by this ticket) -- this test
    only proves compute_betrayal_clan_reputation_update() + apply.py correct
    at the pure-function/apply-path level, not live-pipeline reachability."""
    from src.core.state import ClanState
    from src.core.updates import StateUpdate
    from src.engine.apply import ApplyPath

    contract = ContractService.create_recruitment_contract("c6", 99, 1, tick=100)
    contract = replace(contract, status=ContractStatus.ACTIVE)
    entity = V2EntityBuilder(1).kind("ACTOR").location(0, 0).strategic(contracts={contract.id: contract}).build()

    # Existing entity-level SocialUpdate behavior remains unchanged/additive.
    s_upd, b_upds = ContractService.resolve_contract_outcome(
        entity, contract.id, success=False, betrayal=True, betrayer_id=99
    )
    assert b_upds[1].notoriety_delta == 0.5
    assert b_upds[1].betrayal_increment == 1

    clan = ClanState(clan_id="ironfang", member_entity_ids=(99,), clan_reputation=1.0)
    state = AuthoritativeState(tick=1, seed=0, clans={"ironfang": clan})

    clan_update = ContractService.compute_betrayal_clan_reputation_update(
        betrayer_id=99, state=state, tick=1
    )
    assert clan_update is not None
    assert clan_update.clan_id == "ironfang"
    assert clan_update.clan_reputation_delta < 0.0

    new_state = ApplyPath.apply_partial(state, StateUpdate(clan_updates=[clan_update]))
    assert new_state.clans["ironfang"].clan_reputation < 1.0


def test_contract_betrayal_with_no_clan_produces_no_clan_update():
    """A betrayer with no clan membership produces None, not a crash or an
    erroneous ClanUpdate."""
    state = AuthoritativeState(tick=1, seed=0, clans={})

    clan_update = ContractService.compute_betrayal_clan_reputation_update(
        betrayer_id=99, state=state, tick=1
    )
    assert clan_update is None
