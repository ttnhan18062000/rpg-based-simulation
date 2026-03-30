import pytest
from unittest.mock import MagicMock, patch
from src.core.aspects.progression import ProgressionAspect
from src.core.gameplay.attributes import Attributes, AttributeCaps, train_attributes

def test_genetic_seed_init():
    p = ProgressionAspect(genetic_seed=123)
    p.init_genetics()
    
    assert len(p.aptitudes) == 9
    assert "str" in p.aptitudes
    assert 0.8 <= p.aptitudes["str"] <= 1.25
    assert 50000 <= p.longevity_limit <= 150000

def test_training_uses_aptitudes():
    attrs = Attributes(str_=5, _str_frac=0.0)
    caps = AttributeCaps(str_cap=10)
    
    # 2.0x aptitude (modified code should handle this)
    aptitudes = {"str": 2.0}
    
    # Base rate for attack is 0.015
    # With 2.0x aptitude, it should be 0.03
    train_attributes(attrs, caps, "attack", aptitudes=aptitudes)
    
    assert attrs._str_frac == pytest.approx(0.03)

def test_aging_and_death():
    from src.ai.brain import AIBrain
    config = MagicMock()
    rng = MagicMock()
    brain = AIBrain(config, rng)
    brain._faction_reg = MagicMock()
    
    actor = MagicMock()
    actor.progression.age_ticks = 999
    actor.progression.longevity_limit = 1000
    actor.stats.combat.hp = 10
    actor.stats.combat.hp_ratio = 1.0 # Added to handle perception phase prints if any
    actor.stats.vision_range = 10
    actor.mind.max_attention_slots = 5
    actor.mind.spatial.pos_history = []
    actor.mind.emotional_state = {}
    
    ctx = MagicMock(actor=actor)
    # Mock faction registry to allow check
    brain._faction_reg = MagicMock()
    brain._faction_reg.is_hostile.return_value = False
    actor.spatial.pos.manhattan.return_value = 1
    
    # Mocking Perception.visible_entities as it's called in perception phase
    with patch('src.ai.brain.Perception.visible_entities', return_value=[]):
        brain._sensory_perception_phase(actor, MagicMock())
        brain._memory_appraisal_phase(ctx)
        
        assert actor.progression.age_ticks == 1000
        assert actor.stats.combat.hp == 0
