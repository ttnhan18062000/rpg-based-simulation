"""
tests/unit/domains/progression/test_phase6_progression_events.py

Phase 6 — Progression Trace Events tests.
"""

import pytest
from src.domains.progression.schema import ConversionKind, ConversionOption, ProgressionDecisionResult


def test_conversion_event_contains_selected_and_rejected_options():
    opt1 = ConversionOption(kind=ConversionKind.CRAFT_ITEM, score=0.9, expected_growth_delta=0.6, reason="craft weapon")
    opt2 = ConversionOption(kind=ConversionKind.SELL_LOOT, score=0.7, expected_growth_delta=0.2, reason="sell junk")
    
    decision = ProgressionDecisionResult(
        entity_id=1,
        selected=(opt1,),
        trace={"greed": 0.1, "industry": 0.8, "scored_options": [("CRAFT_ITEM", 0.9), ("SELL_LOOT", 0.7)]},
        reason="craft weapon dominant"
    )
    
    # Event verification: ensure traceback payload has correct elements
    assert decision.entity_id == 1
    assert len(decision.selected) == 1
    assert decision.selected[0].kind == ConversionKind.CRAFT_ITEM
    assert decision.trace["industry"] == 0.8
    assert len(decision.trace["scored_options"]) == 2
