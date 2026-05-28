"""
tests/unit/domains/progression/test_phase6_conversion_decision_service.py

Phase 6 — ConversionDecisionService tests.
"""

import pytest
from src.core.state import AuthoritativeState, PersonalityComponent
from src.core.builder import V2EntityBuilder
from src.domains.progression.schema import ConversionKind, ConversionOption
from src.domains.progression.selector import ConversionDecisionService


def test_selects_equip_when_better_weapon_available():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .identity(personality=PersonalityComponent(greed=0.1, industry=0.1, bravery=0.5)))
    entity = b.build()
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    
    options = (
        ConversionOption(kind=ConversionKind.EQUIP_ITEM, score=0.9, expected_growth_delta=0.8, reason="upgrade weapon"),
        ConversionOption(kind=ConversionKind.SAVE_FOR_LATER, score=0.3, expected_growth_delta=0.0, reason="save")
    )
    
    res = ConversionDecisionService.select(entity, options, state)
    assert len(res.selected) == 1
    assert res.selected[0].kind == ConversionKind.EQUIP_ITEM


def test_greedy_entity_prefers_sell_loot():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         # High greed, low bravery
         .identity(personality=PersonalityComponent(greed=0.9, industry=0.1, bravery=0.5)))
    entity = b.build()
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    
    options = (
        ConversionOption(kind=ConversionKind.SELL_LOOT, score=0.7, expected_growth_delta=0.2, reason="sell"),
        ConversionOption(kind=ConversionKind.CRAFT_ITEM, score=0.75, expected_growth_delta=0.6, reason="craft")
    )
    
    res = ConversionDecisionService.select(entity, options, state)
    assert len(res.selected) == 1
    # Base score of CRAFT_ITEM was 0.75, SELL_LOOT was 0.7. Greedy trait adds bonus to SELL_LOOT, causing it to win.
    assert res.selected[0].kind == ConversionKind.SELL_LOOT
