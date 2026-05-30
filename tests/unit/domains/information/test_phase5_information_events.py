"""
tests/unit/domains/information/test_phase5_information_events.py

Phase 5 — Trace event payloads unit tests.
Verifies diagnostics payload outputs for Information Need, considered sources,
contradictions, and trust entries.
"""

import pytest
from src.domains.information.schema import InformationQuery, NormalizedInformationResponse
from src.domains.information.contradiction import BeliefContradictionResult, LeadCertainty


def test_contradiction_result_trace_fields():
    res = BeliefContradictionResult(
        contradiction_detected=True,
        lead_id="lead_12",
        old_certainty=LeadCertainty.APPROXIMATE,
        new_certainty=LeadCertainty.EXHAUSTED,
        reason="Observation disproved claim.",
    )
    
    assert res.contradiction_detected is True
    assert res.lead_id == "lead_12"
    assert res.old_certainty == LeadCertainty.APPROXIMATE
    assert res.new_certainty == LeadCertainty.EXHAUSTED
    assert res.reason == "Observation disproved claim."
