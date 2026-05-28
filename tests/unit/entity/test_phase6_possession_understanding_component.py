"""
tests/unit/entity/test_phase6_possession_understanding_component.py

Phase 6 — PossessionUnderstandingComponent dataclass tests.
"""

import pytest
from src.domains.progression.schema import PossessionMeaning, PossessionUnderstandingComponent


def test_default_possession_understanding_is_empty():
    comp = PossessionUnderstandingComponent()
    assert len(comp.meanings) == 0
    assert comp.last_evaluated_tick == 0


def test_possession_meaning_fields():
    mean = PossessionMeaning(
        item_id="iron_sword",
        known_uses=("combat",),
        estimated_value=150.0,
        keep_priority=0.8,
        equip_priority=0.9,
    )
    
    assert mean.item_id == "iron_sword"
    assert "combat" in mean.known_uses
    assert mean.estimated_value == 150.0
    assert mean.keep_priority == 0.8
    assert mean.equip_priority == 0.9
