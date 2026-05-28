"""
tests/unit/domains/cooperation/test_phase7_cooperation_postures.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 unit tests verifying unique postures and intent mappings.
"""

import pytest
from src.domains.cooperation.postures import CooperationPosture, get_posture_definition, POSTURE_DEFINITIONS


def test_cooperation_postures_are_unique():
    postures = [p.value for p in CooperationPosture]
    assert len(postures) == len(set(postures))


def test_each_posture_has_definition():
    for posture in CooperationPosture:
        defn = get_posture_definition(posture)
        assert defn.posture == posture
        assert len(defn.description) > 0
        assert len(defn.intent_mapping) > 0


def test_unknown_posture_fails_fast():
    with pytest.raises(ValueError):
        get_posture_definition("INVALID_POSTURE_NAME")
