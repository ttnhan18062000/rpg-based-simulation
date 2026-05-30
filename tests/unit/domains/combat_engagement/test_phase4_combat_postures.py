"""
tests/unit/domains/combat_engagement/test_phase4_combat_postures.py

Phase 4 — Pre-combat posture enums.
"""

import pytest
from src.domains.combat_engagement.schema import CombatPosture


def test_combat_posture_names_are_unique():
    postures = list(CombatPosture)
    assert len(postures) == len(set(postures))


def test_each_posture_has_semantic_mapping():
    expected_values = {
        "ignore",
        "watch",
        "avoid",
        "probe",
        "threaten",
        "engage",
        "skirmish",
        "call_help",
        "retreat",
        "panic_flee",
        "guard_ally",
        "vengeance_engage",
    }
    
    for posture in CombatPosture:
        assert posture.value in expected_values
