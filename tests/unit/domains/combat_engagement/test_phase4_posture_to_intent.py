"""
tests/unit/domains/combat_engagement/test_phase4_posture_to_intent.py

Phase 4 — Posture-to-Intent Bridge unit tests.
Verifies mappings from posture to ActionIntent.
"""

import pytest
from src.domains.combat_engagement.schema import CombatPosture
from src.domains.combat_engagement.resolver import PostureIntentResolver


def test_engage_posture_maps_to_attack_intent():
    intent, strat = PostureIntentResolver.resolve(
        actor_id=1,
        target_id=2,
        posture=CombatPosture.ENGAGE,
        target_pos=(10.0, 15.0),
    )
    
    assert intent is not None
    assert intent.kind == "ATTACK_TARGET"
    assert intent.actor_id == 1
    assert intent.target_id == 2
    assert intent.payload.get("position") == (10.0, 15.0)


def test_retreat_posture_maps_to_retreat_movement_intent():
    intent, strat = PostureIntentResolver.resolve(
        actor_id=1,
        target_id=2,
        posture=CombatPosture.RETREAT,
    )
    
    assert intent is not None
    assert intent.kind == "MOVE_TO"
    assert intent.payload.get("retreat") is True
