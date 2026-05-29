import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, MotivationModel, IdentityDoctrine, ValuePreferenceProfile
from src.domains.motivation.service import MotivationBiasService

def test_motivation_bias_service_doctrine_matching():
    # Setup entity with a doctrine
    doctrine = IdentityDoctrine(
        class_id="warrior",
        preferred_route_tags={"melee": 0.5},
        avoided_route_tags={"flee": 0.8}
    )
    cognition = CognitionModel(motivation=MotivationModel(doctrine=doctrine))
    entity = replace(EntityState(id=1, kind="HERO"), cognition=cognition)
    
    # Target candidate route details
    assert MotivationBiasService.compute_bias_multiplier(entity, ["melee"]) > 1.0
    assert MotivationBiasService.compute_bias_multiplier(entity, ["flee"]) < 1.0
    assert MotivationBiasService.compute_bias_multiplier(entity, ["neutral"]) == 1.0

def test_motivation_bias_service_value_profile():
    # Setup entity with custom values
    values = ValuePreferenceProfile(
        survival=0.8, # high survival -> boosts recovery/flee
        pride=0.9     # high pride -> penalizes help/cooperation
    )
    cognition = CognitionModel(motivation=MotivationModel(values=values))
    entity = replace(EntityState(id=1, kind="HERO"), cognition=cognition)
    
    # Recovery
    assert MotivationBiasService.compute_bias_multiplier(entity, ["recovery"]) > 1.0
    
    # Cooperation
    assert MotivationBiasService.compute_bias_multiplier(entity, ["cooperation"]) < 1.0
