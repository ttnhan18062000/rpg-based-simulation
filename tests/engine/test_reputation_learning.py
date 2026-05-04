import pytest
from dataclasses import replace
from src.core.builder import V2EntityBuilder
from src.core.state import EntityState, AuthoritativeState, IdentityComponent, SocialComponent, StrategicComponent, CombatComponent, InventoryComponent, SocialBond
from src.core.strategic import ContractStatus, ProjectStatus
from src.core.enums import ReasonCode
from src.social.appraisal import SocialAppraisalSystem
from src.social.contracts import ContractService

def test_public_vs_private_trust():
    state = AuthoritativeState(tick=100, seed=42)
    
    # 1. Famous Hero (Public Rep = 1.8)
    hero = (V2EntityBuilder(1)
            .kind("hero")
            .at((0.0, 0.0))
            .social(public_reputation=1.8)
            .build())
    
    # 2. Shady Rogue (Public Rep = 0.4)
    rogue = (V2EntityBuilder(2)
             .kind("rogue")
             .at((0.0, 0.0))
             .social(public_reputation=0.4)
             .build())
    
    # 3. Observer
    observer = (V2EntityBuilder(3)
                .kind("villager")
                .at((5.0, 5.0))
                .hp(100, 100)
                .gold(0)
                .build())
    
    state = replace(state, entities={1: hero, 2: rogue, 3: observer})
    
    # --- SCENARIO 1: No prior bonds ---
    c_hero = ContractService.create_recruitment_contract("c_hero", 1, 3, daily_pay=10, tick=100)
    c_rogue = ContractService.create_recruitment_contract("c_rogue", 2, 3, daily_pay=10, tick=100)
    
    status_hero, reason_hero, _ = SocialAppraisalSystem.appraise_contract(observer, c_hero, state)
    status_rogue, reason_rogue, _ = SocialAppraisalSystem.appraise_contract(observer, c_rogue, state)
    
    # Observer should accept Hero (high public trust)
    assert status_hero == ContractStatus.ACCEPTED
    # Observer should reject Rogue (low public trust)
    assert status_rogue == ContractStatus.CANCELLED
    
    # --- SCENARIO 2: Private Betrayal by Hero ---
    # Mock a strong negative bond due to prior betrayal
    bond_to_hero = SocialBond(target_id=1, sentiment=-0.9)
    observer = replace(observer, social=replace(observer.social, bonds={1: bond_to_hero}))
    
    status_hero_2, reason_hero_2, _ = SocialAppraisalSystem.appraise_contract(observer, c_hero, state)
    
    # Observer should now REJECT Hero because private sentiment takes priority
    assert status_hero_2 == ContractStatus.CANCELLED
    assert reason_hero_2 == ReasonCode.TOTAL_DISTRUST
    
    print("\nSuccessfully verified Public vs Private Trust logic.")
