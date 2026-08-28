"""
Unit tests for SocialContractGoalScorer (TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER).

Covers AC1 (registration), AC2 (metadata carries raw score, never utility, plus contract
identity), the multi-contract reduction rule (investigation.md Risk #3), the preserved 2-of-5
ContractKind coverage (PROTECTION/MERCHANT/POSITION_SWAP never spawn a project), the raw-score
clamp ceiling (Design Decision #3), and the target_pos counterparty-resolution fix
(Design Decision #8) per plan.md Step 6.
"""
from __future__ import annotations

import pytest

from src.ai.goals import GoalRegistry
from src.ai.goals.base import GoalScore
from src.ai.goals.social_contract_scorer import SocialContractGoalScorer
from src.core.builder import V2EntityBuilder
from src.core.models.social import SocialBond
from src.core.state import AuthoritativeState
from src.core.strategic import ContractState, ContractKind, ContractStatus, GoalKind, ProjectKind


def _entity(eid: int = 1, pos: tuple = (0.0, 0.0), trust_history=None, bonds=None):
    builder = V2EntityBuilder(eid).kind("hero").location(*pos)
    if trust_history is not None or bonds is not None:
        builder = builder.social(trust_history=trust_history or {}, bonds=bonds or {})
    return builder.build()


def _state(entities=None, tick=0):
    return AuthoritativeState(tick=tick, seed=42, entities=entities or {})


# --- AC1 ---------------------------------------------------------------------------------


def test_goal_kind_social_contract_is_registered_member():
    assert GoalKind("social_contract") == GoalKind.SOCIAL_CONTRACT
    assert isinstance(GoalRegistry._scorers[GoalKind.SOCIAL_CONTRACT], SocialContractGoalScorer)


def test_social_contract_kind_value_does_not_collide_with_project_kind_or_existing_goal_kind():
    for pk in ProjectKind:
        assert GoalKind.SOCIAL_CONTRACT.value != pk.value, (
            f"GoalKind.SOCIAL_CONTRACT.value must not collide with ProjectKind.{pk.name} "
            f"({pk.value!r}) -- a collision would make intelligence.py's resume/dedup lookup "
            f"(`p.kind == best_candidate.kind`) accidentally match."
        )
    for gk in GoalKind:
        if gk == GoalKind.SOCIAL_CONTRACT:
            continue
        assert GoalKind.SOCIAL_CONTRACT.value != gk.value


def test_social_contract_goal_scorer_implements_goal_scorer_protocol():
    entity = _entity(trust_history={2: 0.8})
    contract = ContractState(
        id="c1", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 20, "duration": 100, "risk_level": "NORMAL"},
        status=ContractStatus.ACTIVE, expiry_tick=50,
    )
    ent = V2EntityBuilder(1).kind("hero").social(trust_history={2: 0.8}).strategic(
        contracts={"c1": contract}
    ).build()
    state = _state(entities={1: ent})
    score = SocialContractGoalScorer().score(ent, state)
    assert isinstance(score, GoalScore)


# --- AC2 -----------------------------------------------------------------------------------


def test_social_contract_goal_scorer_metadata_carries_raw_score_and_contract_identity():
    """
    Worked arithmetic: trust=0.8 (trust_history, no bond), urgency: expiry_tick=50, duration=100,
    current_tick=0 -> ticks_remaining=50 -> urgency=1.0-min(1.0,50/100)=0.5. value: daily_pay=20,
    evolution_level=1 -> expected_pay=10 -> value=min(1.0,20/10)=1.0. risk_level=NORMAL ->
    risk_weight=0.5. raw = 0.8*1.0 + 0.5*1.0 + 1.0*0.9 - 0.5*0.3 = 0.8+0.5+0.9-0.15 = 2.05.
    """
    contract = ContractState(
        id="c1", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 20, "duration": 100, "risk_level": "NORMAL"},
        status=ContractStatus.ACTIVE, expiry_tick=50,
    )
    ent = V2EntityBuilder(1).kind("hero").social(trust_history={2: 0.8}).strategic(
        contracts={"c1": contract}
    ).build()
    state = _state(entities={1: ent}, tick=0)
    score = SocialContractGoalScorer().score(ent, state)

    assert set(score.metadata.keys()) == {
        "contract_id", "source_id", "raw_score", "proj_kind", "obj_kind", "obj_id_prefix",
    }
    assert score.metadata["contract_id"] == "c1"
    assert score.metadata["source_id"] == 2
    assert score.metadata["raw_score"] == pytest.approx(2.05)
    assert score.metadata["proj_kind"] == ProjectKind.COMBAT
    assert score.metadata["raw_score"] != score.utility


# --- AC5 -------------------------------------------------------------------------------------


def test_social_contract_goal_scorer_no_active_contracts_returns_zero_utility_no_target():
    ent = _entity()
    state = _state(entities={1: ent})
    score = SocialContractGoalScorer().score(ent, state)
    assert score.kind == GoalKind.SOCIAL_CONTRACT
    assert score.utility == 0.0
    assert score.target_id is None

    offered = ContractState(
        id="c1", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        status=ContractStatus.OFFERED,
    )
    ent2 = V2EntityBuilder(1).kind("hero").strategic(contracts={"c1": offered}).build()
    state2 = _state(entities={1: ent2})
    score2 = SocialContractGoalScorer().score(ent2, state2)
    assert score2.utility == 0.0
    assert score2.target_id is None


def test_social_contract_protection_merchant_position_swap_never_spawn_a_project():
    for kind in (
        ContractKind.PROTECTION,
        ContractKind.MERCHANT,
        ContractKind.POSITION_SWAP,
        ContractKind.TEAM_UP,
        ContractKind.PAID_INFORMATION,
    ):
        contract = ContractState(
            id=f"c_{kind.value}", kind=kind, source_id=2, target_id=1,
            status=ContractStatus.ACTIVE,
        )
        ent = V2EntityBuilder(1).kind("hero").strategic(contracts={contract.id: contract}).build()
        state = _state(entities={1: ent})
        score = SocialContractGoalScorer().score(ent, state)
        assert score.utility == 0.0, f"{kind} must not spawn a project"
        assert score.target_id is None


# --- Multi-contract reduction (investigation.md Risk #3) -------------------------------------


def test_social_contract_goal_scorer_reduces_multiple_active_contracts_to_one_candidate():
    """
    Worked arithmetic for both candidates (current_tick=0, evolution_level=1):

    RECRUITMENT (c_recruit): trust=0.8 (trust_history), expiry_tick=50, duration=100 ->
    urgency=0.5; daily_pay=20 -> expected_pay=10 -> value=min(1.0,2.0)=1.0; risk_level=NORMAL ->
    risk_weight=0.5. raw = 0.8+0.5+0.9-0.15 = 2.05.

    LOAN (c_loan): trust=0.9 (trust_history), expiry_tick=100, duration=200 ->
    ticks_remaining=100 -> urgency=1.0-min(1.0,100/200)=0.5; amount=100 -> expected_amount=50 ->
    value=min(1.0,2.0)=1.0; risk_weight=0.0 (LOAN carries no risk_level). raw = 0.9+0.5+0.9-0.0 =
    2.3.

    2.3 (LOAN) > 2.05 (RECRUITMENT) -> LOAN's contract ("c_loan") must be the single winner.
    """
    recruit = ContractState(
        id="c_recruit", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 20, "duration": 100, "risk_level": "NORMAL"},
        status=ContractStatus.ACTIVE, expiry_tick=50,
    )
    loan = ContractState(
        id="c_loan", kind=ContractKind.LOAN, source_id=3, target_id=1,
        terms={"amount": 100, "duration": 200},
        status=ContractStatus.ACTIVE, expiry_tick=100,
    )
    ent = V2EntityBuilder(1).kind("hero").social(
        trust_history={2: 0.8, 3: 0.9}
    ).strategic(contracts={"c_recruit": recruit, "c_loan": loan}).build()
    state = _state(entities={1: ent}, tick=0)

    score = SocialContractGoalScorer().score(ent, state)

    assert score.metadata["contract_id"] == "c_loan"
    assert score.metadata["raw_score"] == pytest.approx(2.3)
    assert score.metadata["proj_kind"] == ProjectKind.SOCIAL


# --- Design Decision #3 clamp ceiling ---------------------------------------------------------


def test_social_contract_goal_scorer_raw_score_clamped_to_2_9_ceiling():
    """Not reachable via any real ContractKind combination given the chosen weights (RECRUITMENT
    tops out at 2.87 due to its minimum 0.1 risk_weight; only LOAN's risk_weight=0.0 can reach
    the true 2.9 ceiling: trust=1.0, urgency=1.0, value=1.0, risk_weight=0.0 ->
    1.0+1.0+0.9-0.0=2.9). Asserts the clamp function's boundary behavior directly."""
    ent = V2EntityBuilder(1).kind("hero").social(
        bonds={2: SocialBond(target_id=2, sentiment=1.0)}
    ).build()
    contract = ContractState(
        id="c1", kind=ContractKind.LOAN, source_id=2, target_id=1,
        terms={"amount": 1000, "duration": 100},
        status=ContractStatus.ACTIVE, expiry_tick=100,
    )
    raw = SocialContractGoalScorer._raw_score(ent, contract, current_tick=100)
    assert raw == 2.9


def test_social_contract_goal_scorer_utility_stays_bounded_by_100_after_adventure_fix():
    """TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5: SocialContractGoalScorer
    imports _ADVENTURE_ROUTE_SCORE_MAX/_GOAL_UTILITY_SCORE_MAX from intelligence.py, never from
    adventure_scorer.py -- unaffected by the new dedicated _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX.
    Reuses the raw_score==2.9-clamp-ceiling fixture above, but asserts on the FULL score() call
    path's .utility (not just the _raw_score() helper), proving the implicit 0-100 GoalScore.
    utility bound still holds exactly at the clamp ceiling post-fix."""
    contract = ContractState(
        id="c1", kind=ContractKind.LOAN, source_id=2, target_id=1,
        terms={"amount": 1000, "duration": 100},
        status=ContractStatus.ACTIVE, expiry_tick=100,
    )
    ent = V2EntityBuilder(1).kind("hero").social(
        bonds={2: SocialBond(target_id=2, sentiment=1.0)}
    ).strategic(contracts={"c1": contract}).build()
    state = _state(entities={1: ent, 2: _entity(eid=2)}, tick=100)
    score = SocialContractGoalScorer().score(ent, state)
    assert score.utility == 100.0


# --- Design Decision #8 target_pos resolution --------------------------------------------------


def test_social_contract_target_pos_resolves_to_counterparty_entity_position():
    counterparty = _entity(eid=2, pos=(15.0, 20.0))
    contract = ContractState(
        id="c1", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 20, "duration": 100, "risk_level": "NORMAL"},
        status=ContractStatus.ACTIVE, expiry_tick=50,
    )
    ent = V2EntityBuilder(1).kind("hero").social(trust_history={2: 0.8}).strategic(
        contracts={"c1": contract}
    ).build()
    state = _state(entities={1: ent, 2: counterparty}, tick=0)
    score = SocialContractGoalScorer().score(ent, state)
    assert score.target_pos == counterparty.navigation.position

    state_no_counterparty = _state(entities={1: ent}, tick=0)
    score_absent = SocialContractGoalScorer().score(ent, state_no_counterparty)
    assert score_absent.target_pos is None
