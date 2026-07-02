"""
tests/unit/social/test_parity_soc_134.py

SOC-134: test_social_appraisal_with_narrative
Verifies that public_reputation (a narrative signal) informs social contract appraisal.
High-reputation source → trust threshold met → contract accepted.
Zero-reputation source → trust below 0.2 threshold → TOTAL_DISTRUST rejection.
"""

from dataclasses import replace
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.systems.social_systems.appraisal import SocialAppraisalSystem


def _make_contract(source_id: int, target_id: int) -> ContractState:
    return ContractState(
        id="soc134_test",
        kind=ContractKind.RECRUITMENT,
        source_id=source_id,
        target_id=target_id,
        terms={"daily_pay": 20},
        status=ContractStatus.OFFERED,
    )


class TestSocialAppraisalWithNarrative:
    def test_high_public_reputation_source_accepted(self):
        """SOC-134: narrative-informed appraisal — high-reputation source is trusted."""
        source = (V2EntityBuilder(10)
            .kind("human").location(1, 1)
            .social(public_reputation=2.0)
            .combat(readiness=100.0)
            .build()
        )
        candidate = (V2EntityBuilder(1)
            .kind("human").location(0, 0)
            .combat(hp=100, readiness=0.0)
            .build()
        )

        state = AuthoritativeState(entities={1: candidate, 10: source}, tick=1, seed=1)
        contract = _make_contract(source_id=10, target_id=1)

        status, reason, _ = SocialAppraisalSystem.appraise_contract(candidate, contract, state)
        assert status == ContractStatus.ACCEPTED, (
            f"High-reputation source should be accepted, got status={status} reason={reason}"
        )

    def test_zero_public_reputation_source_rejected(self):
        """SOC-134: narrative-informed appraisal — zero-reputation source triggers total distrust."""
        source = (V2EntityBuilder(10)
            .kind("human").location(1, 1)
            .social(public_reputation=0.0)
            .combat(readiness=100.0)
            .build()
        )
        candidate = (V2EntityBuilder(1)
            .kind("human").location(0, 0)
            .combat(hp=100, readiness=0.0)
            .build()
        )

        state = AuthoritativeState(entities={1: candidate, 10: source}, tick=1, seed=1)
        contract = _make_contract(source_id=10, target_id=1)

        status, reason, _ = SocialAppraisalSystem.appraise_contract(candidate, contract, state)
        assert status == ContractStatus.CANCELLED, (
            f"Zero-reputation source should be rejected, got status={status} reason={reason}"
        )
