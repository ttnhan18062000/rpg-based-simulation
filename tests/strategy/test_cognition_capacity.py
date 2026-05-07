import pytest
from src.core.state import EntityState, AttributeComponent, BiologicalComponent, IdentityComponent, PersonalityComponent
from src.strategy.cognition_capacity import CapacityService

def create_mock_entity(intelligence: int = 5, wisdom: int = 5, perception: int = 5, sleep_debt: float = 0.0):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .attributes(intelligence=intelligence, wisdom=wisdom, perception=perception)
        .biological(sleep_debt=sleep_debt)
        .identity(personality=PersonalityComponent(industry=0.5))
        .build())

def test_base_profile_derivation():
    entity = create_mock_entity(intelligence=10, wisdom=10, perception=10)
    profile = CapacityService.derive_profile(entity)
    
    # Projects: 1 + (10/5) = 3
    assert profile.max_active_projects == 3
    # Leads: 4 + (10/3) = 7
    assert profile.max_leads == 7
    # Concerns: 3 + (10/4) = 5
    assert profile.max_concerns == 5

def test_high_intelligence_scaling():
    entity = create_mock_entity(intelligence=20, wisdom=5, perception=5)
    profile = CapacityService.derive_profile(entity)
    
    # Detour breadth/depth should scale
    assert profile.detour_breadth >= 3
    assert profile.detour_depth >= 2

def test_fatigue_penalty():
    # Fresh entity
    fresh = create_mock_entity(intelligence=10, wisdom=10, sleep_debt=0.0)
    fresh_profile = CapacityService.derive_profile(fresh)
    
    # Tired entity
    tired = create_mock_entity(intelligence=10, wisdom=10, sleep_debt=80.0)
    tired_profile = CapacityService.derive_profile(tired)
    
    # Tired entity should have halved limits
    assert tired_profile.max_active_projects < fresh_profile.max_active_projects
    assert tired_profile.max_leads < fresh_profile.max_leads

def test_determinism():
    entity = create_mock_entity(intelligence=15, wisdom=15)
    profile1 = CapacityService.derive_profile(entity)
    profile2 = CapacityService.derive_profile(entity)
    
    assert profile1 == profile2
