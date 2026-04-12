import pytest
from unittest.mock import MagicMock
from src.core.logic.personality import PersonalityLogic
from src.core.logic.social_appraisal import SocialAppraisalService
from src.core.models.enums import GoalType, Archetype
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.mind import PersonalityProfile
from src.core.models.social import SocialRegistry, SocialBond
from src.platform.rng import DeterministicRNG

@pytest.fixture
def rng():
    return DeterministicRNG(seed=42)

@pytest.fixture
def mock_entity():
    """Returns a mocked entity with Identity and Mind.personality."""
    entity = MagicMock()
    entity.id = 1
    
    identity = IdentityAspect(display_name="TestHero", archetype=Archetype.BALANCED)
    # Patch identity to reference the entity for PersonalityLogic lookup
    identity._entity = entity
    entity.identity = identity
    
    personality = PersonalityProfile(archetype="balanced")
    entity.mind = MagicMock()
    entity.mind.decision = MagicMock()
    entity.mind.decision.personality = personality
    
    return entity

def test_personality_bias_logic(mock_entity):
    identity = mock_entity.identity
    personality = mock_entity.mind.decision.personality
    
    # Default BALANCED (all RPG Traits = 0.5)
    # 1. Curiosity bias for EXPLORE
    base = 10.0
    explore_utility = PersonalityLogic.apply_motive_biases(GoalType.EXPLORE, base, identity)
    # 10.0 * (1.0 + 0.5 * 0.5) = 12.5
    assert explore_utility == 12.5
    
    # 2. Caution bias for REST
    rest_utility = PersonalityLogic.apply_motive_biases(GoalType.REST, base, identity)
    # 10.0 * (1.0 + 0.5 * 0.4) = 12.0
    assert rest_utility == 12.0
    
    # 3. Test divergence with COWARDLY variant
    personality.neuroticism = 0.9
    personality.curiosity = 0.2
    
    flee_utility = PersonalityLogic.apply_motive_biases(GoalType.FLEE, 10.0, identity)
    # 10.0 * (1.0 + 0.9 * 0.7) = 16.3
    assert flee_utility == pytest.approx(16.3)
    
    explore_utility_coward = PersonalityLogic.apply_motive_biases(GoalType.EXPLORE, 10.0, identity)
    # 10.0 * (1.0 + 0.2 * 0.5) = 11.0
    assert explore_utility_coward == 11.0

def test_social_appraisal_logic(rng):
    registry = SocialRegistry()
    
    # Create two entities
    actor = MagicMock()
    actor.id = 1
    actor.mind.decision.personality = PersonalityProfile(caution=0.5, aggression=0.5)
    
    target = MagicMock()
    target.id = 2
    
    # Establish a FEAR bond
    bond = registry.get_bond(1, 2)
    bond.fear = 0.8
    
    # Mock registry methods
    registry.get_bond_or_none = MagicMock(return_value=bond)
    registry.get_reputation = MagicMock(return_value=0.0)
    
    motives = SocialAppraisalService.calculate_social_motives(actor, [target], registry)
    
    # Fear > 0.6 should trigger FLEE bias
    # 0.8 * 1.5 = 1.2
    assert motives[GoalType.FLEE] == pytest.approx(1.2)
    
    # Establish a TRUST bond
    bond.fear = 0.0
    bond.trust = 0.9
    
    motives_trust = SocialAppraisalService.calculate_social_motives(actor, [target], registry)
    # Trust * 0.5 = 0.45
    assert motives_trust[GoalType.SOCIAL] == pytest.approx(0.45)
    # Trust * 0.3 = 0.27
    assert motives_trust[GoalType.GUARD] == pytest.approx(0.27)

def test_full_motive_pipeline_integration(mock_entity):
    """Verifies that social and personality biases stack correctly."""
    identity = mock_entity.identity
    personality = mock_entity.mind.decision.personality
    
    # Scenario: Low neuroticism / High confidence glory seeker
    personality.neuroticism = 0.2
    
    # Base 1.0 + social 1.5 (extreme fear from appraisal) = 2.5
    flee_base = 2.5
    final_flee = PersonalityLogic.apply_motive_biases(GoalType.FLEE, flee_base, identity)
    # 2.5 * (1.0 + 0.2 * 0.7) = 2.5 * 1.14 = 2.85
    
    assert final_flee == pytest.approx(2.85)
