import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, IdentityComponent, SocialComponent, StrategicComponent
from src.core.strategic import ContractStatus, DirectiveKind, TurningPointKind
from src.social.contracts import ContractService
from src.core.builder import V2EntityBuilder

def test_contract_betrayal_consequences():
    state = AuthoritativeState(tick=100, seed=42)
    
    # 1. Source (ID 1) recruits Target (ID 2)
    source_builder = (V2EntityBuilder(1)
                      .kind("hero")
                      .location(0, 0)
                      .identity(faction=1))
    
    target_builder = (V2EntityBuilder(2)
                      .kind("hero")
                      .location(1, 1)
                      .identity(faction=2))
    
    contract = ContractService.create_recruitment_contract("c1", 1, 2, tick=100)
    
    # Accept contract
    contract = replace(contract, status=ContractStatus.ACCEPTED)
    # Make ACTIVE
    contract = replace(contract, status=ContractStatus.ACTIVE)
    
    source = source_builder.strategic(contracts={"c1": contract}).build()
    target = target_builder.strategic(contracts={"c1": contract}).build()
    
    # 2. Source betrays Target
    strat_up, social_ups = ContractService.resolve_contract_outcome(
        target, "c1", success=False, betrayal=True, betrayer_id=1, tick=105
    )
    
    # Verify StrategicUpdate
    assert strat_up.contracts_add_or_update[0].status == ContractStatus.BETRAYED
    assert strat_up.directives_add_or_update[0].kind == DirectiveKind.COMBAT
    assert strat_up.directives_add_or_update[0].target == "1"
    assert strat_up.turning_points_add[0].kind == TurningPointKind.BETRAYAL
    assert strat_up.turning_points_add[0].subject_id == 1
    
    # Verify SocialUpdate for Target (how they view Source)
    target_social_up = social_ups[0] 
    
    assert target_social_up.bond_updates[0].target_id == 1
    assert target_social_up.bond_updates[0].sentiment_delta == -1.0
    
    print("\nSuccessfully verified Betrayal consequences (Directive, TurningPoint, Sentiment).")
