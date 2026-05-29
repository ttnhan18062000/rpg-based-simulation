"""
src/observability/reporter.py
───────────────────────────────────────────────────────────────────────────────
CausalityChainReporter for Phase 17.
"""

from __future__ import annotations

class CausalityChainReporter:
    """Reconstructs and formats full end-to-end cognitive decision causal chains."""

    @staticmethod
    def generate_chain(
        perceived_signal: str,
        decision_kind: str,
        action_intent: str,
        result_success: bool
    ) -> str:
        outcome = "SUCCESS" if result_success else "FAILURE"
        return f"[Perception: {perceived_signal}] -> [Cognition: {decision_kind}] -> [Intent: {action_intent}] -> [Authoritative Result: {outcome}]"
