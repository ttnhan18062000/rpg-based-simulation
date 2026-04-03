import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import AIBrain
from src.core.models.enums import AIState, Faction
from src.core.models import Vector2

@pytest.fixture
def brain():
    config = MagicMock()
    rng = MagicMock()
    return AIBrain(config, rng)

def test_perception_phase_populates_attention_pool(brain):
    # Setup
    actor = MagicMock()
    actor.spatial.pos = Vector2(0, 0)
    actor.stats.spatial.vision_range = 10
    actor.mind.max_attention_slots = 3
    actor.mind.attention_pool = []
    actor.identity.faction = Faction.HERO_GUILD
    
    # Mock snapshot with many entities
    snapshot = MagicMock()
    
    # 5 Entities at different distances
    # Dist 1 (High priority)
    e1 = MagicMock(id=101, pos=Vector2(1, 0), faction=Faction.GOBLIN_HORDE)
    # Dist 2 (Hostile)
    e2 = MagicMock(id=102, pos=Vector2(2, 0), faction=Faction.GOBLIN_HORDE)
    # Dist 5 (Neutral)
    e3 = MagicMock(id=103, pos=Vector2(5, 0), faction=Faction.HERO_GUILD)
    # Dist 10 (Edge of vision)
    e4 = MagicMock(id=104, pos=Vector2(10, 0), faction=Faction.GOBLIN_HORDE)
    # Dist 20 (Outside vision)
    e5 = MagicMock(id=105, pos=Vector2(20, 0), faction=Faction.GOBLIN_HORDE)
    
    with patch('src.ai.perception.Perception.visible_entities', return_value=[e1, e2, e3, e4]):
        # Run perception
        brain._sensory_perception_phase(actor, snapshot)
        
        # Should have exactly 3 slots (max_attention_slots)
        assert len(actor.mind.attention_pool) == 3
        
        # Highly salient entities should be first (e1, e2)
        assert 101 in actor.mind.attention_pool
        assert 102 in actor.mind.attention_pool
        # e4 should be excluded as it's the furthest  goblin
