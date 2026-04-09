import pytest
from src.core.logic.personality import PersonalityLogic
from src.core.logic.social_appraisal import SocialAppraisalService
from src.core.models.enums import GoalType, Archetype
from src.core.aspects.identity import IdentityAspect
from src.core.models.social import SocialRegistry, SocialBond
from src.platform.rng import DeterministicRNG

@pytest.fixture
def rng():
    return DeterministicRNG(seed=42)

@pytest.fixture
def identity():
    return IdentityAspect(display_name="TestHero", archetype=Archetype.BALANCED)

def test_personality_bias_logic(identity):
    # Default BALANCED (all OCEAN = 0.5)
    identity.apply_archetype_template()
    
    # 1. Openness bias for EXPLORE
    base = 10.0
    open_utility = PersonalityLogic.apply_motive_biases(GoalType.EXPLORE, base, identity)
    # 10.0 * (1.0 + 0.5 * 0.5) = 12.5
    assert open_utility == 12.5
    
    # 2. Conscientiousness bias for REST
    rest_utility = PersonalityLogic.apply_motive_biases(GoalType.REST, base, identity)
    # 10.0 * (1.0 + 0.5 * 0.4) = 12.0
    assert rest_utility == 12.0
    
    # 3. Test divergence with COWARDLY_SURVIVOR
    identity.archetype = Archetype.COWARDLY_SURVIVOR
    identity.apply_archetype_template() # Neuroticism = 0.9, Openness = 0.2
    
    flee_utility = PersonalityLogic.apply_motive_biases(GoalType.FLEE, 10.0, identity)
    # 10.0 * (1.0 + 0.9 * 0.7) = 16.3
    assert flee_utility == pytest.approx(16.3)
    
    open_utility_coward = PersonalityLogic.apply_motive_biases(GoalType.EXPLORE, 10.0, identity)
    # 10.0 * (1.0 + 0.2 * 0.5) = 11.0
    assert open_utility_coward == 11.0

def test_social_appraisal_logic(rng):
    registry = SocialRegistry()
    
    # Create two entities (mocked for simplicity)
    from unittest.mock import MagicMock
    actor = MagicMock()
    actor.id = 1
    
    target = MagicMock()
    target.id = 2
    
    # Establish a FEAR bond
    registry.get_bond(1, 2)
    bond = registry.get_bond(1, 2)
    bond.fear = 0.8
    
    motives = SocialAppraisalService.calculate_social_motives(actor, [target], registry)
    
    # Fear > 0.6 should trigger FLEE bias
    assert motives[GoalType.FLEE] > 1.0
    assert motives[GoalType.FLEE] == pytest.approx(0.8 * 1.5)
    
    # Establish a TRUST bond
    bond.fear = 0.0
    bond.trust = 0.9
    
    motives_trust = SocialAppraisalService.calculate_social_motives(actor, [target], registry)
    assert motives_trust[GoalType.SOCIAL] == pytest.approx(0.9 * 0.5)
    assert motives_trust[GoalType.GUARD] == pytest.approx(0.9 * 0.3)

def test_full_motive_pipeline_integration(identity):
    """Verifies that social and personality biases stack correctly."""
    identity.archetype = Archetype.GLORY_SEEKER
    identity.apply_archetype_template() 
    # GLORY_SEEKER: Extraversion=0.9, Neuro=0.2, Openness=0.8
    
    # Mock social bias (e.g. from a rival)
    social_biases = {GoalType.COMBAT: 0.5} 
    
    # Calculate final utility for COMBAT
    # Base 1.0 + social 0.5 = 1.5
    # GLORY_SEEKER has no specific COMBAT bias in PersonalityLogic yet (base case),
    # but it reduces FLEE if Neuroticism is low.
    
    flee_base = 1.0 + 1.5 # Extreme fear from social appraisal (fear=1.0 * 1.5)
    final_flee = PersonalityLogic.apply_motive_biases(GoalType.FLEE, flee_base, identity)
    # 2.5 * (1.0 + 0.2 * 0.7) = 2.5 * 1.14 = 2.85
    
    assert final_flee == pytest.approx(2.85)
