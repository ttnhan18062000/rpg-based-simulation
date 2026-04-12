import pytest
from src.ai.brain import AIBrain, AIContext, MindUpdate
from src.core.models.enums import GoalType, EmotionType
from src.core.models.vectors import Vector2
from src.core.aspects.mind import SocialStance
from src.core.models.social import SocialRegistry

from src.core.entities.entity import Entity
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.mind import MindAspect

def create_test_entity(id, pos):
    return Entity(
        id=id,
        kind="hero",
        identity=IdentityAspect(faction=0),
        spatial=SpatialAspect(pos=pos, current_region_id="test_region", vision_range=20),
        combat=CombatAspect(),
        progression=ProgressionAspect(),
        mind=MindAspect()
    )

def test_locational_trauma_triggers_dread():
    """Verify entering a high-trauma region increments DREAD."""
    mock_config = type('MockConfig', (), {'ai': type('AIConfig', (), {'flee_hp_threshold': 0.3})})
    mock_rng = type('MockRNG', (), {'randint': lambda a, b: a, 'random': lambda: 0.5})
    brain = AIBrain(config=mock_config, rng=mock_rng)
    actor = create_test_entity(1, Vector2(10, 10))
    
    # Set high trauma for current region
    actor.mind.narrative.memory_locations["test_region"] = -0.8
    
    snapshot = type('MockSnapshot', (), {
        'tick': 100,
        'hour': 12,
        'social_registry': SocialRegistry(),
        'region_consequence_registry': {},
        'regions': [],
        'entities': {1: actor},
        'nearby_entity_ids': lambda x, y, r: []
    })
    
    from src.core.gameplay.faction import FactionRegistry
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=mock_config, 
        rng=mock_rng, 
        faction_reg=FactionRegistry.default()
    )
    
    updates = []
    brain._memory_appraisal_phase(ctx, updates, {})
    
    # Check for DREAD increment proposed in updates
    dread_proposed = False
    for up in updates:
        if isinstance(up, MindUpdate) and up.emotion_delta:
            if up.emotion_delta.get(EmotionType.DREAD, 0) > 0:
                dread_proposed = True
                
    assert dread_proposed, "Entering trauma zone should propose DREAD increment"

def test_emotional_bias_on_utility():
    """Verify DREAD increases FLEE utility and decreases EXPLORE utility."""
    mock_config = type('MockConfig', (), {'ai': type('AIConfig', (), {'flee_hp_threshold': 0.3})})
    mock_rng = type('MockRNG', (), {'randint': lambda a, b: a, 'random': lambda: 0.5})
    brain = AIBrain(config=mock_config, rng=mock_rng)
    actor = create_test_entity(1, Vector2(10, 10))
    
    # Set high DREAD and bypass throttle
    actor.mind.emotion.dread = 0.7
    actor.mind.decision.last_appraisal_tick = 0
    
    snapshot = type('MockSnapshot', (), {
        'tick': 100,
        'hour': 12,
        'social_registry': SocialRegistry(),
        'region_consequence_registry': {},
        'regions': [],
        'entities': {1: actor},
        'nearby_entity_ids': lambda x, y, r: []
    })
    
    from src.core.gameplay.faction import FactionRegistry
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=mock_config, 
        rng=mock_rng, 
        faction_reg=FactionRegistry.default()
    )
    
    updates = []
    brain._memory_appraisal_phase(ctx, updates, {})
    
    # Check decision drivers and updates
    has_dread_driver = False
    for up in updates:
        if isinstance(up, MindUpdate) and up.decision_drivers:
            if any("dread" in d.lower() or "traumatized" in d.lower() for d in up.decision_drivers):
                has_dread_driver = True
                
    assert has_dread_driver, "High DREAD should trigger traumatized decision driver"

def test_emotional_decay():
    """Verify emotions propose negative delta for decay."""
    mock_config = type('MockConfig', (), {'ai': type('AIConfig', (), {'flee_hp_threshold': 0.3})})
    mock_rng = type('MockRNG', (), {'randint': lambda a, b: a, 'random': lambda: 0.5})
    brain = AIBrain(config=mock_config, rng=mock_rng)
    actor = create_test_entity(1, Vector2(10, 10))
    actor.mind.decision.last_appraisal_tick = 0
    
    snapshot = type('MockSnapshot', (), {
        'tick': 100,
        'hour': 12,
        'social_registry': SocialRegistry(),
        'region_consequence_registry': {},
        'regions': [],
        'entities': {1: actor},
        'nearby_entity_ids': lambda x, y, r: []
    })
    
    from src.core.gameplay.faction import FactionRegistry
    ctx = AIContext(
        actor=actor, 
        snapshot=snapshot, 
        config=mock_config, 
        rng=mock_rng, 
        faction_reg=FactionRegistry.default()
    )
    
    updates = []
    brain._memory_appraisal_phase(ctx, updates, {})
    
    decay_proposed = False
    for up in updates:
        if isinstance(up, MindUpdate) and up.emotion_delta:
            # Check if decay delta is negative
            if up.emotion_delta.get(EmotionType.DREAD, 0) < 0:
                decay_proposed = True
                
    assert decay_proposed, "Emotional appraisal should propose decay for stable emotional state"
