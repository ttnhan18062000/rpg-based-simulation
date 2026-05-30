import pytest
from src.observability.trace import DecisionTrace, DecisionOptionTrace, RejectedOptionTrace

def test_decision_trace_contract():
    trace = DecisionTrace(
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
    assert trace.decision_id == "dec_1"
    assert trace.selected_option == "engage"
