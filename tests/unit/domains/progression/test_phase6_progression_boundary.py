"""
tests/unit/domains/progression/test_phase6_progression_boundary.py

Phase 6 — Progression and Reward boundary tests.
"""

import pytest
from src.domains.progression.schema import ConversionKind, ConversionOption


def test_conversion_option_primitive_checks():
    opt = ConversionOption(
        kind=ConversionKind.CRAFT_ITEM,
        score=0.9,
        expected_growth_delta=0.4,
        cost_gold=10,
        reason="Test craft",
    )
    
    assert opt.kind == ConversionKind.CRAFT_ITEM
    assert opt.score == 0.9
    assert opt.expected_growth_delta == 0.4
    assert opt.cost_gold == 10


def test_progression_service_does_not_mutate_state():
    # Verify progression conversion operations do not directly mutate live actor attributes
    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState
    from src.domains.progression.phase import ProgressionConversionPhase
    from src.core.updates import StateUpdate
    
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    update = StateUpdate()
    
    refined_update = ProgressionConversionPhase.execute(state, update)
    
    # Original state is intact, only proposed updates are returned
    assert entity.inventory.gold == 0
    assert 1 in refined_update.entity_updates
