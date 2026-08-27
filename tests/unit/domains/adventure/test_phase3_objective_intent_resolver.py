"""
tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py

Phase 3 — ObjectiveIntentResolver unit tests.
Verifies resolving of first objective into adapted ActionIntent targets.
"""

import pytest
from src.core.strategic import ObjectiveState, ObjectiveKind, ObjectiveStatus
from src.domains.adventure.resolver import ObjectiveIntentResolver
from src.engine.intent.action_intent import ActionIntent


def test_resolves_reach_service_to_move_to():
    obj = ObjectiveState(
        id="obj.rec.1",
        kind=ObjectiveKind.REACH_SERVICE,
        target="tavern_1",
        target_position=(10.0, 20.0),
        status=ObjectiveStatus.UNRESOLVED,
        blocker_ids=[],
    )
    
    intent = ObjectiveIntentResolver.resolve(entity_id=42, objective=obj)
    
    assert intent.kind == "MOVE_TO"
    assert intent.actor_id == 42
    assert intent.target_id == "tavern_1"
    assert intent.payload.get("position") == (10.0, 20.0)
    assert intent.source_opportunity_id == "obj.rec.1"


def test_resolves_buy_item_to_buy_item():
    obj = ObjectiveState(
        id="obj.buy.1",
        kind=ObjectiveKind.BUY_ITEM,
        target="potion_merchant",
        target_position=None,
        status=ObjectiveStatus.UNRESOLVED,
        blocker_ids=[],
    )
    
    intent = ObjectiveIntentResolver.resolve(
        entity_id=42,
        objective=obj,
        payload={"item_id": "health_potion", "gold_cost": 50},
    )
    
    assert intent.kind == "BUY_ITEM"
    assert intent.actor_id == 42
    assert intent.target_id == "potion_merchant"
    assert intent.payload.get("item_id") == "health_potion"
    assert intent.payload.get("gold_cost") == 50


def test_resolves_change_occupation_to_change_occupation():
    """TCK-20260824-OCCUPATION-CHANGE-TRIGGER, plan.md Step 6."""
    obj = ObjectiveState(
        id="obj.career.1",
        kind=ObjectiveKind.CHANGE_OCCUPATION,
        target="role_1",
        target_position=(3.0, 4.0),
        status=ObjectiveStatus.UNRESOLVED,
        blocker_ids=[],
    )

    intent = ObjectiveIntentResolver.resolve(entity_id=42, objective=obj, payload={})

    assert intent.kind == "CHANGE_OCCUPATION"
    assert intent.actor_id == 42
    assert intent.target_id == "role_1"
