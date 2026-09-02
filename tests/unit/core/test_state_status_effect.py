"""
TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION

Schema-only coverage for the new StatusEffectState typed record, following the
WoundState/ScarState precedent: frozen dataclass, default field values, and
plain-dict serialization via dataclasses.asdict (matching how
CombatComponent.to_canonical_dict() serializes wounds/scars).
"""
from dataclasses import FrozenInstanceError, asdict

import pytest

from src.core.state import StatusEffectState


def test_status_effect_state_is_frozen():
    effect = StatusEffectState(kind="frozen")
    with pytest.raises(FrozenInstanceError):
        effect.kind = "stunned"


def test_status_effect_state_default_field_values():
    effect = StatusEffectState(kind="frozen")
    assert effect.kind == "frozen"
    assert effect.source == ""
    assert effect.magnitude == 0.0
    assert effect.expires_tick == -1


def test_status_effect_state_asdict_round_trip():
    effect = StatusEffectState(kind="stunned", source="test_fixture", magnitude=0.5, expires_tick=100)
    d = asdict(effect)
    assert d == {
        "kind": "stunned",
        "source": "test_fixture",
        "magnitude": 0.5,
        "expires_tick": 100,
    }
