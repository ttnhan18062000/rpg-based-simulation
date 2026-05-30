"""
tests/unit/domains/information/test_phase5_information_response_normalizer.py

Phase 5 — InformationResponseNormalizer unit tests.
"""

import pytest
from src.domains.information.schema import InformationQuery
from src.domains.information.normalizer import InformationResponseNormalizer


def test_normalize_known_fact():
    q = InformationQuery(subject="iron_ore", kind="material_source")
    raw = {
        "answer_kind": "KNOWN_FACT",
        "certainty": 0.95,
        "details": {"location": "old_mine"},
    }
    
    res = InformationResponseNormalizer.normalize(q, "guide_1", raw)
    assert res.answer_kind == "KNOWN_FACT"
    assert len(res.facts) == 1
    assert res.facts[0].details.get("location") == "old_mine"
    assert res.certainty == 0.95


def test_normalize_partial_lead():
    q = InformationQuery(subject="moon_resin", kind="material_source")
    raw = {
        "answer_kind": "PARTIAL_LEAD",
        "certainty": 0.6,
        "details": {"clue_location": "north_ruin"},
    }
    
    res = InformationResponseNormalizer.normalize(q, 2, raw)
    assert res.answer_kind == "PARTIAL_LEAD"
    assert len(res.leads) == 1
    assert res.leads[0].detail == "north_ruin"
    assert res.leads[0].source_entity_id == 2
