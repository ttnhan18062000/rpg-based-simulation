import pytest
from src.observability.trace import DecisionTrace, DecisionOptionTrace, RejectedOptionTrace
from src.observability.validator import DecisionTraceValidator

def test_decision_trace_validator():
    # Complete valid trace
    trace_valid = DecisionTrace(
        decision_id="dec_1",
        entity_id=1,
        decision_kind="combat_engagement",
        noticed=("enemy_1",),
        known=("enemy_weakness",),
        needs=("survival",),
        capability_refs=("slash",),
        considered_options=(DecisionOptionTrace(name="engage", score=0.8),),
        selected_option="engage",
        rejected_options=(RejectedOptionTrace(name="flee", reason="high_confidence"),),
        reason="high_confidence",
        expected_effects=("victory",)
    )
    assert DecisionTraceValidator.validate(trace_valid, mode="STRICT") is True

    # Incomplete trace missing selected option
    trace_invalid = DecisionTrace(
        decision_id="dec_2",
        entity_id=1,
        decision_kind="combat_engagement",
        noticed=(),
        known=(),
        needs=(),
        capability_refs=(),
        considered_options=(),
        selected_option=None,
        rejected_options=(),
        reason="",
        expected_effects=()
    )
    assert DecisionTraceValidator.validate(trace_invalid, mode="STRICT") is False
