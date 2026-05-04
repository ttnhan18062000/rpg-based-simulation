import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, GroupRecord, SocialBond
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.core.updates import StateUpdate, EntityUpdate
from src.social.contracts import ContractService
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath

def create_mock_entity(eid: int, gold: int = 10, hp: int = 100):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("hero")
        .at((0, 0))
        .with_class("hero")
        .with_combat(hp=hp, max_hp=100, atk=10, def_stat=5, alive=True)
        .with_inventory(gold=gold)
        .build()
    )

def test_contract_expiration_resolves_and_dissolves():
    # 1. Setup Leader and Member
    leader = create_mock_entity(1)
    member = create_mock_entity(2)
    
    # 2. Setup Active Contract (expired)
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=2,
        status=ContractStatus.ACTIVE,
        created_tick=10,
        expiry_tick=50
    )
    
    # Add contract to both
    leader = replace(leader, strategic=replace(leader.strategic, contracts={"c1": contract}))
    member = replace(member, strategic=replace(member.strategic, contracts={"c1": contract}))
    
    # 3. Setup Group tied to contract
    group = GroupRecord(
        id=1001,
        leader_id=1,
        member_ids={1, 2},
        anchor=(0, 0),
        contract_id="c1",
        last_updated_tick=10
    )
    
    state = AuthoritativeState(
        tick=51, # Past expiry
        entities={1: leader, 2: member},
        groups={1001: group},
        seed=42
    )
    
    # 4. Run Pipeline
    update = StateUpdate()
    update = AuthoritativeApplyPipeline.refine(state, update)
    
    # Verify Contract Status changed in update
    l_upd = update.entity_updates.get(1)
    m_upd = update.entity_updates.get(2)
    
    assert l_upd is not None
    assert m_upd is not None
    
    # Contract should be COMPLETED (default for success in process_active_contracts)
    l_contract = next((c for c in l_upd.strategic.contracts_add_or_update if c.id == "c1"), None)
    assert l_contract.status == ContractStatus.COMPLETED
    
    # Verify trust/reputation updates (heroism_delta = 0.05 on success)
    assert l_upd.social.heroism_delta == 0.05
    assert m_upd.social.heroism_delta == 0.05
    
    # Apply update to see group dissolution
    final_state = ApplyPath.apply_generation(state, update)
    
    # Group should be dissolved because contract is no longer ACTIVE
    assert 1001 not in final_state.groups

def test_contract_betrayal_consequences():
    # 1. Setup
    leader = create_mock_entity(1)
    member = create_mock_entity(2)
    contract = ContractState(id="c1", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.ACTIVE)
    leader = replace(leader, strategic=replace(leader.strategic, contracts={"c1": contract}))
    
    # 2. Resolve with Betrayal by Leader (1)
    strat_up, social_ups = ContractService.resolve_contract_outcome(leader, contract.id, success=False, betrayal=True, betrayer_id=1)
    
    assert strat_up.contracts_add_or_update[0].status == ContractStatus.BETRAYED
    
    # Verify Avenge Directive (targeted at betrayer 1)
    from src.core.strategic import DirectivePriority
    avenge = next((d for d in strat_up.directives_add_or_update if d.kind == "combat"), None)
    assert avenge is not None
    assert avenge.target == "1"
    assert avenge.priority == DirectivePriority.HIGH
    
    # Verify Reputation and Betrayal Count
    source_social = social_ups[0]
    target_social = social_ups[1]
    
    assert source_social.notoriety_delta == 0.5
    assert source_social.betrayal_increment == 1
    assert target_social.notoriety_delta == 0.1 
    
    # Verify Bond Sentiment (distrust)
    assert source_social.bond_updates[0].sentiment_delta == -1.0
    assert target_social.bond_updates[0].sentiment_delta == -1.0
