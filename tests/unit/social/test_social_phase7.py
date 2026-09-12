import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, GroupRecord, SocialBond
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.core.updates import StateUpdate, EntityUpdate
from src.systems.social_systems.contracts import ContractService
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath

def create_mock_entity(eid: int, gold: int = 10, hp: int = 100):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0, 0)
        .identity(class_id="hero")
        .combat(hp=hp, max_hp=100, atk=10, def_stat=5, alive=True)
        .inventory(gold=gold)
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

    # Contract lives only on the offering/source entity's own record -- matching the real
    # production invariant (never mirrored to the target). Storing it on both used to mask a
    # real double-fire between two competing resolution mechanisms
    # (TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION); resolve_expirations() is now
    # the sole owner, so a mirrored copy would independently double-count within that single
    # mechanism's own per-entity loop -- an artifact of the test construction, not of production
    # reality.
    leader = replace(leader, strategic=replace(leader.strategic, contracts={"c1": contract}))

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
        tick=51, # Past expiry -- deliberately skips the exact expiry tick, kept as a regression
                 # guard against the double-fire this construction once exposed.
        entities={1: leader, 2: member},
        groups={1001: group},
        seed=42
    )

    # 4. Run Pipeline
    update = StateUpdate(force_full_scan=True)
    update = AuthoritativeApplyPipeline.refine(state, update)

    # Verify Contract Status changed in update
    l_upd = update.entity_updates.get(1)
    m_upd = update.entity_updates.get(2)

    assert l_upd is not None
    assert m_upd is not None

    # Contract should be COMPLETED (resolve_expirations() is the sole owner of contract-expiry
    # resolution; ContractService.process_active_contracts(), the prior duplicate, was deleted)
    l_contract = next((c for c in l_upd.strategic.contracts_add_or_update if c.id == "c1"), None)
    assert l_contract.status == ContractStatus.COMPLETED

    # Single-fire consequences to BOTH parties (heroism_delta = 0.05, not the old double-fire
    # value of 0.1). The member never held its own contract record, and never triggered a second
    # resolution -- it received its consequence purely because resolve_expirations() now applies
    # BOTH SocialUpdates resolve_contract_outcome() returns, not only the contract-holder's own
    # (the bug the deleted process_active_contracts() also carried).
    assert l_upd.social.heroism_delta == 0.05
    assert m_upd.social.heroism_delta == 0.05

    # Apply update to see group dissolution
    final_state = ApplyPath.apply_generation(state, update)

    # Group should be dissolved because contract is no longer ACTIVE
    assert 1001 not in final_state.groups


def test_contract_expiration_grants_the_other_party_its_own_real_consequence():
    """
    Direct regression test for the bug found while implementing
    TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION: the deleted
    ContractService.process_active_contracts() computed a SocialUpdate for both the contract
    holder AND the other party (resolve_contract_outcome() returns [entity_up, other_up]), but
    only ever applied the holder's own half -- the other party never received its consequence at
    any call site, ever, in the codebase's history. This asserts the fix precisely: exact values
    on BOTH sides, not just presence.
    """
    leader = create_mock_entity(1)
    member = create_mock_entity(2)

    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=2,
        status=ContractStatus.ACTIVE,
        created_tick=10,
        expiry_tick=50,
    )
    leader = replace(leader, strategic=replace(leader.strategic, contracts={"c1": contract}))

    state = AuthoritativeState(
        tick=50,  # Exact expiry tick -- the real, non-skipped production case.
        entities={1: leader, 2: member},
        groups={},
        seed=42,
    )

    update = StateUpdate(force_full_scan=True)
    update = AuthoritativeApplyPipeline.refine(state, update)

    l_upd = update.entity_updates.get(1)
    m_upd = update.entity_updates.get(2)

    assert l_upd is not None
    assert m_upd is not None

    # Source (contract holder): heroism reward, and a bond update toward the target.
    assert l_upd.social.heroism_delta == 0.05
    assert l_upd.social.notoriety_delta == 0.0
    assert len(l_upd.social.bond_updates) == 1
    l_bond = l_upd.social.bond_updates[0]
    assert l_bond.target_id == 2
    assert l_bond.sentiment_delta == 0.2
    assert l_bond.familiarity_delta == 0.1

    # Target (the other party): the same real reward, symmetric bond update back toward the
    # source -- this is the half that never worked before this fix.
    assert m_upd.social.heroism_delta == 0.05
    assert m_upd.social.notoriety_delta == 0.0
    assert len(m_upd.social.bond_updates) == 1
    m_bond = m_upd.social.bond_updates[0]
    assert m_bond.target_id == 1
    assert m_bond.sentiment_delta == 0.2
    assert m_bond.familiarity_delta == 0.1

    # The target never held its own contract record -- no strategic update should exist for it.
    assert m_upd.strategic is None

def test_social_phase7_betrayal_consequences():
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
