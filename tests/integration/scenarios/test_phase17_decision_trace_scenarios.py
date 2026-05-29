import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, EmotionalModel, SubjectiveModel, SelfModel, RecoveryState
from src.observability.trace import DecisionTrace, DecisionOptionTrace, RejectedOptionTrace
from src.observability.validator import DecisionTraceValidator
from src.observability.reporter import CausalityChainReporter

def test_combat_loss_has_full_causal_trace():
    # Survived near death -> records causal elements
    trace = DecisionTrace(
        decision_id="dec_combat_1",
        entity_id=1,
        decision_kind="combat_engagement",
        noticed=("wolf",),
        known=("damaged_sword",),
        needs=("survival",),
        capability_refs=("slash",),
        considered_options=(
            DecisionOptionTrace(name="engage", score=0.3),
            DecisionOptionTrace(name="flee", score=0.8)
        ),
        selected_option="flee",
        rejected_options=(RejectedOptionTrace(name="engage", reason="low_health"),),
        reason="low_health",
        expected_effects=("safety",)
    )

    assert DecisionTraceValidator.validate(trace, mode="STRICT") is True

    # Build reportable chain
    chain = CausalityChainReporter.generate_chain(
        perceived_signal="wolf_near",
        decision_kind="combat_engagement",
        action_intent="FLEE",
        result_success=True
    )
    assert "wolf_near" in chain
    assert "combat_engagement" in chain
    assert "FLEE" in chain

def test_cooperation_betrayal_has_full_causal_trace():
    # Betrayal choice traces back to high greed / low pride
    trace = DecisionTrace(
        decision_id="dec_coop_1",
        entity_id=1,
        decision_kind="cooperation_decision",
        noticed=("chest", "ally_in_danger"),
        known=(),
        needs=("greed",),
        capability_refs=(),
        considered_options=(
            DecisionOptionTrace(name="help", score=0.2),
            DecisionOptionTrace(name="loot", score=0.9)
        ),
        selected_option="loot",
        rejected_options=(RejectedOptionTrace(name="help", reason="high_greed"),),
        reason="high_greed",
        expected_effects=("gold",)
    )

    assert DecisionTraceValidator.validate(trace, mode="STRICT") is True
