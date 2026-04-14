import pytest
from unittest.mock import MagicMock
from src.ai.cognition_capacity import CognitionCapacityBuilder

def create_mock_entity(int_=1, wis=1, per=1, cha=1, int_cap=15, wis_cap=15, per_cap=15, cha_cap=15, stamina=50, max_stamina=50):
    attributes = MagicMock()
    attributes.int_ = int_
    attributes.wis = wis
    attributes.per = per
    attributes.cha = cha
    
    caps = MagicMock()
    caps.int_cap = int_cap
    caps.wis_cap = wis_cap
    caps.per_cap = per_cap
    caps.cha_cap = cha_cap
    
    progression = MagicMock()
    progression.attributes = attributes
    progression.attribute_caps = caps
    progression.stamina = stamina
    progression.max_stamina = max_stamina
    
    entity = MagicMock()
    entity.progression = progression
    return entity

def test_build_profile_min_attributes_full_stamina():
    # Case A — minimum attributes, full stamina
    ent = create_mock_entity(int_=1, wis=1, per=1, cha=1)
    profile = CognitionCapacityBuilder.build(ent)
    
    assert profile.planning_budget == 3
    assert profile.judgment_stability == 0.350
    assert profile.evidence_quality == 0.300
    assert profile.social_bandwidth == 2
    assert profile.detour_depth_limit == 1
    assert profile.active_slice_limit == 3
    assert profile.concern_intake_limit == 2
    assert profile.lead_retention_limit == 2
    assert profile.candidate_zone_limit == 1
    assert profile.ally_evaluation_limit == 2
    assert profile.blocker_resolution_patience == 0.300
    assert profile.resume_reliability == 0.250
    assert profile.interruption_resistance == 0.200
    assert profile.abandonment_threshold_mod == 0.800
    assert profile.contradiction_sensitivity == 0.200
    assert profile.source_trust_learning_rate == 0.100

def test_build_profile_max_attributes_full_stamina():
    # Case B — maximum attributes, full stamina
    ent = create_mock_entity(int_=15, wis=15, per=15, cha=15)
    profile = CognitionCapacityBuilder.build(ent)
    
    assert profile.planning_budget == 9
    assert profile.judgment_stability == 0.900
    assert profile.evidence_quality == 0.950
    assert profile.social_bandwidth == 7
    assert profile.detour_depth_limit == 4
    assert profile.active_slice_limit == 9
    assert profile.concern_intake_limit == 5
    assert profile.lead_retention_limit == 7
    assert profile.candidate_zone_limit == 5
    assert profile.ally_evaluation_limit == 7
    assert profile.blocker_resolution_patience == 0.900
    assert profile.resume_reliability == 0.950
    assert profile.interruption_resistance == 0.800
    assert profile.abandonment_threshold_mod == 1.100
    assert profile.contradiction_sensitivity == 0.800
    assert profile.source_trust_learning_rate == 0.750

def test_build_profile_max_attributes_half_stamina():
    # Case C — maximum attributes, half stamina
    ent = create_mock_entity(int_=15, wis=15, per=15, cha=15, stamina=25, max_stamina=50)
    profile = CognitionCapacityBuilder.build(ent)
    
    # Fatigue = 1 - 0.5 = 0.5
    # judgment_stability: 0.35 + 0.45*1 + 0.10*1 - 0.20*0.5 = 0.35 + 0.45 + 0.1 - 0.1 = 0.8
    assert profile.judgment_stability == 0.800
    assert profile.evidence_quality == 0.850
    assert profile.blocker_resolution_patience == 0.800
    assert profile.resume_reliability == 0.850
    # interruption_resistance: 0.20 + 0.45*1 + 0.15*1 - 0.15*0.5 = 0.2 + 0.45 + 0.15 - 0.075 = 0.725
    assert profile.interruption_resistance == 0.725
    # abandonment_threshold_mod: 0.80 + 0.30*1 - 0.10*0.5 = 0.8 + 0.3 - 0.05 = 1.05
    assert profile.abandonment_threshold_mod == 1.050
    
    # Budgets should match Case B
    assert profile.planning_budget == 9

def test_build_profile_uses_attribute_caps():
    # Test normalization with non-default caps
    ent = create_mock_entity(int_=10, wis=1, per=1, cha=1, int_cap=10) # n_int = (10-1)/(10-1) = 1.0
    profile = CognitionCapacityBuilder.build(ent)
    
    # with n_int = 1.0 and others at 1 (n=0)
    # planning_budget = 3 + 5*1 + 1*0 = 8
    assert profile.planning_budget == 8

class MissingAttrs:
    pass

def test_build_profile_handles_missing_attributes():
    # Test fallback to 1
    progression = MagicMock()
    progression.attributes = MissingAttrs() # No int_, wis, etc.
    progression.attribute_caps = MissingAttrs() # No caps
    progression.stamina = 50
    progression.max_stamina = 50
    
    entity = MagicMock()
    entity.progression = progression
    
    profile = CognitionCapacityBuilder.build(entity)
    assert profile.planning_budget == 3 # Same as Case A

def test_build_profile_handles_missing_caps():
    # Test fallback to 15
    attributes = MissingAttrs()
    attributes.int_ = 1
    attributes.wis = 1
    attributes.per = 1
    attributes.cha = 1
    
    progression = MagicMock()
    progression.attributes = attributes
    progression.attribute_caps = MissingAttrs() # No caps
    progression.stamina = 50
    progression.max_stamina = 50
    
    entity = MagicMock()
    entity.progression = progression
    
    profile = CognitionCapacityBuilder.build(entity)
    assert profile.planning_budget == 3 # Same as Case A


def test_build_profile_handles_zero_max_stamina():
    # Test fallback to stamina ratio 1.0
    ent = create_mock_entity(int_=1, stamina=5, max_stamina=0)
    profile = CognitionCapacityBuilder.build(ent)
    
    # judgment_stability at min attributes (n=0) and fatigue=0 (sr=1.0)
    # result should be same as Case A
    assert profile.judgment_stability == 0.350

