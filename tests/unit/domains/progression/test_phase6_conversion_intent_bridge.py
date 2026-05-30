"""
tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py

Phase 6 — ConversionIntentResolver tests.
"""

import pytest
from src.core.state import AuthoritativeState, ItemStack, EquipSlot
from src.core.builder import V2EntityBuilder
from src.domains.progression.schema import ConversionKind, ConversionOption, ProgressionDecisionResult
from src.domains.progression.resolver import ConversionIntentResolver


def test_craft_conversion_maps_to_blacksmith_craft_intent():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    
    decision = ProgressionDecisionResult(
        entity_id=1,
        selected=(ConversionOption(kind=ConversionKind.CRAFT_ITEM, score=0.9, expected_growth_delta=0.6, reason="craft"),)
    )
    
    upd = ConversionIntentResolver.resolve(entity, decision, state)
    assert upd.task is not None
    assert upd.task.work_kind_set == "BLACKSMITH_CRAFT"
    assert upd.task.payload_set.get("recipe") == "iron_sword"


def test_allocate_ap_conversion_maps_to_allocate_ap_intent():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    
    decision = ProgressionDecisionResult(
        entity_id=1,
        selected=(ConversionOption(kind=ConversionKind.ALLOCATE_AP, score=0.85, expected_growth_delta=0.5, reason="allocate"),)
    )
    
    upd = ConversionIntentResolver.resolve(entity, decision, state)
    assert upd.identity is not None
    assert upd.identity.unspent_ap_delta == -1
