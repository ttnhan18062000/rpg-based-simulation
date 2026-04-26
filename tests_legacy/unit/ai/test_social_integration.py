import pytest
from src_legacy.ai.brain import AIBrain, AIContext, MindUpdate
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.enums import AIState, GoalType, Faction, HeroClass
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.aspects.mind import MindAspect, PersonalityProfile
from src_legacy.core.models.social import SocialRegistry
from src_legacy.core.models.snapshot import Snapshot

class MockEntity:
    def __init__(self, id, pos, faction=Faction.HERO_GUILD):
        self.id = id
        self.spatial = type('Spatial', (), {'pos': pos, 'current_region_id': "test_region", 'vision_range': 10})
        self.combat = type('Combat', (), {'hp': 100, 'max_hp': 100, 'hp_ratio': 1.0})
        self.mind = MindAspect()
        self.mind.perception.vision_range = 10
        self.progression = type('Progression', (), {'age_ticks': 0, 'longevity_limit': 1000})
        self.identity = type('Identity', (), {'faction': faction, 'tier': 1, 'hero_class': HeroClass.WARRIOR, 'archetype': 0})
        self.inventory = type('Inventory', (), {'main_hand': None, 'off_hand': None, 'weapon': ""})

def test_social_bias_on_goal_scoring():
    """Verify that a high-trust bond increases SOCIAL goal score."""
    mock_config = type('MockConfig', (), {'ai': type('AIConfig', (), {'memory_limit': 100})})
    mock_rng = type('MockRNG', (), {'randint': lambda a, b: a, 'random': lambda: 0.5})
    brain = AIBrain(config=mock_config, rng=mock_rng)
    actor = MockEntity(1, Vector2(10, 10))
    actor.mind.decision.last_appraisal_tick = 0
    friend = MockEntity(2, Vector2(11, 11))
    
    registry = SocialRegistry()
    bond = registry.get_bond(actor.id, friend.id)
    bond.trust = 1.1 # Direct set for deterministic test
    
    # Snapshot requires many args, let's mock it partially
    snapshot = type('MockSnapshot', (), {
        'tick': 100,
        'social_registry': registry,
        'entities': {1: actor, 2: friend},
        'nearby_entity_ids': lambda x, y, r: [2]
    })
    
    from src_legacy.core.gameplay.faction import FactionRegistry
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=mock_config, 
        rng=mock_rng, 
        faction_reg=FactionRegistry.default(),
        _visible_override=[friend]
    )
    
    # Update brain to run appraisal (All motive logic is now here in Phase 1/2)
    from src_legacy.core.logic.social_appraisal import SocialAppraisalService
    social_biases = SocialAppraisalService.calculate_social_motives(actor, [friend], registry)
    updates = []
    brain._memory_appraisal_phase(ctx, updates, social_biases)
    
    # Apply MindUpdate to actor
    has_social_driver = False
    for up in updates:
        if isinstance(up, MindUpdate):
            if up.social_update:
                actor.mind.social = up.social_update
            if up.decision_drivers:
                if any("social" in d.lower() or "bond" in d.lower() for d in up.decision_drivers):
                    has_social_driver = True
            
    # Verify bias was calculated
    assert actor.mind.social.social_utility_biases[GoalType.SOCIAL] >= 0.5
    assert has_social_driver, f"Decision drivers should include social factors, got drivers in updates"

def test_reputation_impact_on_caution():
    """Verify low global reputation triggers defensive posture in cautious entities."""
    mock_config = type('MockConfig', (), {'ai': type('AIConfig', (), {'memory_limit': 100})})
    mock_rng = type('MockRNG', (), {'randint': lambda a, b: a, 'random': lambda: 0.5})
    brain = AIBrain(config=mock_config, rng=mock_rng)
    actor = MockEntity(1, Vector2(10, 10))
    actor.mind.decision.personality.caution = 1.0 # Max caution
    
    villain = MockEntity(2, Vector2(12, 12), faction=Faction.GOBLIN_HORDE)
    
    registry = SocialRegistry()
    registry.update_reputation(villain.id, -50) # Very bad reputation
    
    # Snapshot requires many args, let's mock it partially
    snapshot = type('MockSnapshot', (), {
        'tick': 100,
        'social_registry': registry,
        'entities': {1: actor, 2: villain},
        'nearby_entity_ids': lambda x, y, r: [2]
    })
    
    from src_legacy.core.gameplay.faction import FactionRegistry
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=mock_config, 
        rng=mock_rng, 
        faction_reg=FactionRegistry.default(),
        _visible_override=[villain]
    )
    
    from src_legacy.core.logic.social_appraisal import SocialAppraisalService
    social_biases = SocialAppraisalService.calculate_social_motives(actor, [villain], registry)
    updates = []
    brain._memory_appraisal_phase(ctx, updates, social_biases)
    for up in updates:
        if isinstance(up, MindUpdate) and up.social_update:
            actor.mind.social = up.social_update
            
    # Verify FLEE bias is increased due to reputation + caution
    assert actor.mind.social.social_utility_biases[GoalType.FLEE] > 0
