import pytest
from src.core.cognition import RoleFitPreference

def test_role_fit_preference_serialization():
    role_fit = RoleFitPreference(
        weapon_tags={"melee": 1.0},
        armor_tags={"heavy": 0.8}
    )
    d = role_fit.to_canonical_dict()
    assert d["weapon_tags"]["melee"] == 1.0
    assert d["armor_tags"]["heavy"] == 0.8
