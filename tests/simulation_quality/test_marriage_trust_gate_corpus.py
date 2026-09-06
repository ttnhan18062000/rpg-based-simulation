"""Idea 33 (Marriage) corpus proof (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS).

CORRECTION, found during Investigate: the real marriage gate is NOT `familiarity >= 0.6` -- that
figure actually belongs to idea 13's Team-Up gate (`_appraise_team_up`), in the same file. Real
mechanism: `_appraise_marriage()` (src/systems/social_systems/appraisal.py:372-382) uses ONLY the
shared trust-prelude (trust_score < 0.2, or bond.sentiment < -0.8 -> CANCELLED; betrayal-history
check) and always ACCEPTS once that prelude passes -- no marriage-specific threshold exists. There
is also no PROPOSED->ACCEPTED transition to observe: `execute_propose_marriage()`
(src/engine/domain/core_actions.py:401-453) creates `MarriageState` directly at
`status=MarriageStatus.ACCEPTED` in one action once the shared trust gate passes.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.models.social import SocialBond
from src.core.state import AuthoritativeState
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.systems.social_systems.appraisal import SocialAppraisalSystem


def _marriage_contract(source_id: int, target_id: int) -> ContractState:
    return ContractState(
        id="temp_eval", kind=ContractKind.MARRIAGE, source_id=source_id, target_id=target_id,
        terms={}, status=ContractStatus.OFFERED, created_tick=0,
    )


def test_marriage_accepted_once_shared_trust_prelude_passes():
    # bond.sentiment = 0.0 -> trust_score = 0.5, well above the 0.2 distrust floor.
    proposer = V2EntityBuilder(2).location(0.0, 0.0).social(
        bonds={1: SocialBond(target_id=1, sentiment=0.0, familiarity=0.1)}
    ).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: V2EntityBuilder(1).location(0.0, 0.0).build(), 2: proposer})

    status, reason, _ = SocialAppraisalSystem.appraise_contract(
        proposer, _marriage_contract(1, 2), state
    )
    assert status == ContractStatus.ACCEPTED, f"expected ACCEPTED at trust_score=0.5, got {status}/{reason}"


def test_marriage_cancelled_when_target_holds_total_distrust():
    # bond.sentiment = -0.9 -> trust_score = 0.05 < 0.2 distrust floor.
    distrustful = V2EntityBuilder(2).location(0.0, 0.0).social(
        bonds={1: SocialBond(target_id=1, sentiment=-0.9, familiarity=0.9)}
    ).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: V2EntityBuilder(1).location(0.0, 0.0).build(), 2: distrustful})

    status, reason, _ = SocialAppraisalSystem.appraise_contract(
        distrustful, _marriage_contract(1, 2), state
    )
    assert status == ContractStatus.CANCELLED, f"expected CANCELLED at total distrust, got {status}/{reason}"
