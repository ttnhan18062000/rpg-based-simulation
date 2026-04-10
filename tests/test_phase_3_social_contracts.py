import pytest
import uuid
from unittest.mock import MagicMock
from src.core.models.enums import OfferStatus, ContractKind, StrategicStatus, GoalType
from src.core.models.strategy import ProjectRecord, ContractTermRecord, RecruitmentOfferRecord, SocialContractRecord
from src.ai.strategy.recruitment_negotiation import RecruitmentNegotiationService
from src.ai.strategy.contract_outcome import ContractOutcomeService
from src.ai.strategy.objective_to_goal_mapper import ObjectiveToGoalMapper
from src.core.models.lived_structure import GroupRecord
from src.core.aspects.mind import DecisionDriver
from src.actions.base import SocialUpdate, ReputationUpdate, StrategicUpdate

from types import SimpleNamespace

@pytest.fixture
def custom_mock_ctx():
    # Use SimpleNamespace for more deterministic attribute behavior than MagicMock
    actor = SimpleNamespace(id=1)
    actor.mind = SimpleNamespace(
        decision=SimpleNamespace(personality=SimpleNamespace(greed=0.5), motives=[]),
        social=SimpleNamespace(known_bonds={}),
        strategic=SimpleNamespace(directives=[])
    )
    actor.identity = SimpleNamespace(
        reputation=SimpleNamespace(trustworthiness=5, heroism_score=5),
        group_id=None
    )
    actor.combat = SimpleNamespace(hp_ratio=1.0)
    
    ctx = SimpleNamespace(
        snapshot=SimpleNamespace(tick=100, entities={1: actor}, group_registry={}),
        actor=actor,
        group=None # Default to no group
    )
    return ctx

def test_recruitment_haggling_threshold(custom_mock_ctx):
    """Verify that candidates counter-offer when willingness is close to threshold."""
    # 1. Setup a candidate who is slightly below the 0.3 threshold
    candidate = custom_mock_ctx.actor
    candidate.mind.decision.personality.greed = 0.8 # Greedy candidate wants more
    
    # 2. Setup an offer with low payout (20%) but negotiable
    recruiter = MagicMock()
    recruiter.id = 2
    recruiter.identity.reputation.trustworthiness = 5
    recruiter.identity.reputation.heroism_score = 5
    custom_mock_ctx.snapshot.entities[2] = recruiter
    
    offer = RecruitmentOfferRecord(
        offer_id="off_test",
        recruiter_id=2,
        candidate_id=1,
        contract_kind=ContractKind.EXPEDITION,
        status=OfferStatus.PENDING,
        proposed_terms=[
            ContractTermRecord(
                term_type="payout",
                label="Low Payout",
                params={"value": 0.2, "is_negotiable": True}
            )
        ],
        negotiation_count=0
    )
    
    # 3. Evaluate
    appraisal = RecruitmentNegotiationService.evaluate_offer(custom_mock_ctx, offer)
    
    # Expected: COUNTERED because greed makes them want more 
    # expected_share = 0.2 + 0.8*0.3 = 0.44
    # counter_payout = round(0.44 + (0.8 * 0.1), 2) = 0.52
    assert appraisal.status == OfferStatus.COUNTERED
    assert appraisal.reason == "Haggling for better payout"
    # Find the payout term in counter_terms
    payout_term = next(t for t in appraisal.counter_terms if t.term_type == "payout")
    assert payout_term.params["value"] == 0.52

def test_contract_outcome_consequences():
    """Verify that contract resolution returns correct intent updates for all members."""
    contract = SocialContractRecord(
        contract_id="ct_test",
        founder_id=1,
        member_ids=[1, 2],
        member_roles={1: "vanguard", 2: "support"},
        kind=ContractKind.EXPEDITION,
        purpose="Verify consequences",
        terms=[]
    )
    
    # 1. Resolve as RESOLVED (Success)
    updates = ContractOutcomeService.resolve_contract(contract, StrategicStatus.RESOLVED, tick=500)
    
    # Founder (ID 1) should have reputation and relationship updates
    f_updates = updates[1]
    assert any(isinstance(u, ReputationUpdate) and u.trustworthiness_delta > 0 for u in f_updates)
    assert any(isinstance(u, SocialUpdate) and u.target_id == 2 and u.trust_delta > 0 for u in f_updates)
    
    # Check StrategicUpdate (marked as RESOLVED)
    strat_update = next(u for u in f_updates if isinstance(u, StrategicUpdate))
    assert strat_update.contracts_add_or_update[0].status == StrategicStatus.RESOLVED
    assert strat_update.contracts_add_or_update[0].resolved_tick == 500

def test_role_aware_tactical_biases(custom_mock_ctx):
    """Verify that utility biases change based on contract role."""
    from src.core.models.strategy import ProjectRecord, ObjectiveKind, ProjectRecord
    
    obj = MagicMock()
    obj.kind = ObjectiveKind.TRAIN
    obj.objective_id = "test_obj"
    obj.project_id = "test_proj"
    obj.leads = [] # Fix for Task 9 scaling
    
    # 1. Setup Vanguard Role
    group = GroupRecord(
        group_id="grp_test",
        leader_id=2,
        member_ids={1, 2},
        member_roles={1: "vanguard", 2: "support"}
    )
    custom_mock_ctx.group = group
    custom_mock_ctx.actor.identity.group_id = "grp_test"
    custom_mock_ctx.snapshot.group_registry["grp_test"] = group
    
    # 2. Get biases
    vanguard_biases = ObjectiveToGoalMapper.get_tactical_biases(custom_mock_ctx, obj)
    
    # 3. Setup Support Role (swap roles)
    group.member_roles[1] = "support"
    support_biases = ObjectiveToGoalMapper.get_tactical_biases(custom_mock_ctx, obj)
    
    # Verification
    assert vanguard_biases[GoalType.COMBAT] > support_biases[GoalType.COMBAT]
    assert support_biases[GoalType.SOCIAL] > vanguard_biases[GoalType.SOCIAL]
