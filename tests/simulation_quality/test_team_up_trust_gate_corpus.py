"""Idea 13 (Trade & Team-Up) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS):
`ContractKind.TEAM_UP` (not a `TeamUpInvite` class -- that identifier does not exist anywhere in
src/) is gated by SocialAppraisalSystem._appraise_team_up()'s real trust_score >= 0.6 threshold.
Real production path: appraise_contract() called directly, the same pure-function call shape this
M9 batch's own sibling ticket (CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS) already established for
appraisal-pipeline-shaped assertions.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.models.social import SocialBond
from src.core.state import AuthoritativeState
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.systems.social_systems.appraisal import SocialAppraisalSystem


def _team_up_contract(source_id: int, target_id: int) -> ContractState:
    return ContractState(
        id="temp_eval", kind=ContractKind.TEAM_UP, source_id=source_id, target_id=target_id,
        terms={"risk_level": "NORMAL"}, status=ContractStatus.OFFERED, created_tick=0,
    )


def test_team_up_accepted_when_trust_score_at_or_above_0_6():
    # bond.sentiment = 0.4 -> trust_score = (0.4 + 1.0) / 2.0 = 0.7 >= 0.6
    trusting = V2EntityBuilder(2).location(0.0, 0.0).social(
        bonds={1: SocialBond(target_id=1, sentiment=0.4, familiarity=0.9)}
    ).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: V2EntityBuilder(1).location(0.0, 0.0).build(), 2: trusting})

    status, reason, _ = SocialAppraisalSystem.appraise_contract(
        trusting, _team_up_contract(1, 2), state
    )
    assert status == ContractStatus.ACCEPTED, f"expected ACCEPTED at trust_score=0.7, got {status}/{reason}"


def test_team_up_declined_when_trust_score_below_0_6():
    # bond.sentiment = -0.4 -> trust_score = (-0.4 + 1.0) / 2.0 = 0.3 < 0.6
    distrustful = V2EntityBuilder(2).location(0.0, 0.0).social(
        bonds={1: SocialBond(target_id=1, sentiment=-0.4, familiarity=0.9)}
    ).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: V2EntityBuilder(1).location(0.0, 0.0).build(), 2: distrustful})

    status, reason, _ = SocialAppraisalSystem.appraise_contract(
        distrustful, _team_up_contract(1, 2), state
    )
    assert status == ContractStatus.CANCELLED, f"expected CANCELLED at trust_score=0.3, got {status}/{reason}"
