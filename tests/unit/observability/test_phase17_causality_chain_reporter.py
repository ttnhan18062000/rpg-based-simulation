import pytest
from src.observability.reporter import CausalityChainReporter

def test_causality_chain_reporter():
    chain = CausalityChainReporter.generate_chain(
        perceived_signal="enemy_near",
        decision_kind="combat_engagement",
        action_intent="ATTACK",
        result_success=True
    )
    assert "enemy_near" in chain
    assert "combat_engagement" in chain
    assert "ATTACK" in chain
