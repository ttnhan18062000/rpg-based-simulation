import pytest
from src.core.cognition import IdentityDoctrine, ValuePreferenceProfile, RoleFitPreference, MotivationModel

def test_identity_doctrine_serialization():
    doctrine = IdentityDoctrine(
        class_id="warrior",
        preferred_route_tags={"melee": 0.8, "heavy_armor": 0.5},
        avoided_route_tags={"ranged": 0.9},
        combat_style_bias={"aggressive": 0.7},
        cooperation_bias={"solo": 0.2}
    )
    d = doctrine.to_canonical_dict()
    assert d["class_id"] == "warrior"
    assert d["preferred_route_tags"]["melee"] == 0.8
    assert d["preferred_route_tags"]["heavy_armor"] == 0.5
    assert d["avoided_route_tags"]["ranged"] == 0.9

def test_value_preference_profile_defaults():
    profile = ValuePreferenceProfile()
    assert profile.survival == 0.5
    assert profile.reward == 0.5
    assert profile.knowledge == 0.5
    assert profile.loyalty == 0.5
    assert profile.pride == 0.5
    assert profile.curiosity == 0.5
    assert profile.caution == 0.5
    
    d = profile.to_canonical_dict()
    assert d["survival"] == 0.5
    assert d["pride"] == 0.5

def test_role_fit_preference_serialization():
    role_fit = RoleFitPreference(
        weapon_tags={"melee": 1.0},
        armor_tags={"heavy": 0.8}
    )
    d = role_fit.to_canonical_dict()
    assert d["weapon_tags"]["melee"] == 1.0
    assert d["armor_tags"]["heavy"] == 0.8
