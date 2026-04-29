import pytest
from dataclasses import replace
from src.core.state import EntityState, SocialComponent, InteractionComponent, IdentityComponent, AttributeComponent, InventoryComponent, StrategicComponent, CombatComponent, EquipmentComponent, NavigationComponent, TaskComponent, StaminaComponent, BiologicalComponent, LifecycleComponent, AptitudeComponent, BetrayalRecord
from src.core.strategic import ContractState, ContractKind, ContractStatus, StrategicComponent
from src.systems.social_contract import SocialContractSystem
from src.social.appraisal import SocialAppraisalSystem
from src.systems.party import PartyCoordinationSystem
from src.core.updates import StrategicUpdate, SocialUpdate

@pytest.fixture
def base_entity():
    return EntityState(
        id=1,
        kind="hero",
        position=(0, 0),
        social=SocialComponent(),
        strategic=StrategicComponent(),
        combat=CombatComponent(),
        inventory=InventoryComponent(),
        identity=IdentityComponent(),
        attributes=AttributeComponent(),
        interaction=InteractionComponent(),
        navigation=NavigationComponent(),
        task=TaskComponent(),
        stamina=StaminaComponent(),
        biological=BiologicalComponent(),
        lifecycle=LifecycleComponent(),
        aptitude=AptitudeComponent()
    )

def test_contract_state_machine_valid():
    contract = ContractState(id="c1", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.OFFERED)
    entity = EntityState(id=2, kind="hero", position=(0,0), strategic=StrategicComponent(contracts={"c1": contract}))
    
    # Valid: OFFERED -> ACCEPTED
    upd = SocialContractSystem.transition_contract(entity, "c1", ContractStatus.ACCEPTED, 100)
    assert len(upd.contracts_add_or_update) == 1
    assert upd.contracts_add_or_update[0].status == ContractStatus.ACCEPTED

def test_contract_state_machine_invalid():
    contract = ContractState(id="c1", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.OFFERED)
    entity = EntityState(id=2, kind="hero", position=(0,0), strategic=StrategicComponent(contracts={"c1": contract}))
    
    # Invalid: OFFERED -> FULFILLED
    upd = SocialContractSystem.transition_contract(entity, "c1", ContractStatus.FULFILLED, 100)
    assert len(upd.contracts_add_or_update) == 0

def test_recruitment_appraisal_trust_impact(base_entity):
    # Offerer has high trust
    offerer_id = 10
    social = base_entity.social
    social = replace(social, trust_history={offerer_id: 0.9})
    entity = replace(base_entity, social=social)
    
    contract = ContractState(id="c1", kind=ContractKind.RECRUITMENT, source_id=offerer_id, target_id=1, terms={"daily_pay": 50})
    
    status, reason, _ = SocialAppraisalSystem.appraise_contract(entity, contract, None)
    assert status == ContractStatus.ACCEPTED
    assert reason == "FAIR_COMPENSATION"

def test_recruitment_appraisal_low_trust(base_entity):
    # Offerer has very low trust
    offerer_id = 10
    social = base_entity.social
    social = replace(social, trust_history={offerer_id: 0.1})
    entity = replace(base_entity, social=social)
    
    contract = ContractState(id="c1", kind=ContractKind.RECRUITMENT, source_id=offerer_id, target_id=1, terms={"daily_pay": 100})
    
    status, reason, _ = SocialAppraisalSystem.appraise_contract(entity, contract, None)
    assert status == ContractStatus.CANCELLED
    assert reason == "TOTAL_DISTRUST"

def test_betrayal_consequences(base_entity):
    betrayer_id = 10
    victim = base_entity
    
    social_upd, strat_upd = SocialAppraisalSystem.process_betrayal(victim, betrayer_id, salience=1.0, current_tick=100)
    
    # 1. Trust drop
    assert social_upd.trust_delta[betrayer_id] < -0.5
    assert social_upd.betrayal_increment == 1
    
    # 2. Strategic Turning Point & Avenge Directive
    assert len(strat_upd.turning_points_add) == 1
    assert strat_upd.turning_points_add[0].kind == "betrayal"
    assert any(d.kind == "avenge" for d in strat_upd.directives_add_or_update)

def test_party_leadership_influence(base_entity):
    leader_id = 10
    contract = ContractState(id="c1", kind=ContractKind.RECRUITMENT, source_id=leader_id, target_id=1, status=ContractStatus.ACTIVE)
    entity = replace(base_entity, strategic=replace(base_entity.strategic, contracts={"c1": contract}))
    
    # Leader has an objective
    from src.core.strategic import ObjectiveState, ProjectState
    leader_obj = ObjectiveState(id="obj1", kind="HARVEST", target="node1")
    leader_proj = ProjectState(id="proj1", kind="HARVEST", objectives=[leader_obj], active_objective_id="obj1")
    leader = replace(base_entity, id=leader_id, strategic=replace(base_entity.strategic, projects={"proj1": leader_proj}, current_project_id="proj1"))
    
    from src.core.state import AuthoritativeState
    state = AuthoritativeState(entities={1: entity, leader_id: leader}, tick=100, seed=42)
    
    scores = PartyCoordinationSystem.apply_leadership_influence(entity, state, [])
    
    # Check if leader's objective was injected as a candidate
    assert len(scores) == 1
    assert scores[0].kind == "HARVEST"
    assert scores[0].target_id == "node1"
    assert scores[0].metadata["party_sync"] is True
