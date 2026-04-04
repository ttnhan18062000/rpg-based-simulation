import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock, patch
from src.core.aspects.progression import ProgressionAspect
from src.core.models.vectors import Vector2
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
    config.flee_hp_threshold = 0.2
    rng = MagicMock()
    brain = AIBrain(config, rng)
    
    actor = MagicMock()
    actor.id = 1
    actor.kind = "hero"
    actor.identity.faction = "hero_guild"
    from src.core.aspects.progression import ProgressionAspect
    from src.core.aspects.combat import CombatAspect
    from src.core.aspects.mind import MindAspect
    
    actor.progression = ProgressionAspect(age_ticks=999, longevity_limit=1000)
    actor.combat = CombatAspect(hp=10, max_hp=10)
    actor.mind = MindAspect()
    actor.mind.emotion.mood = 0.5
    actor.spatial.pos = Vector2(x=0, y=0)
    actor.spatial.current_region_id = None
    actor.spatial.vision_range = 10
    actor.mind.navigation.pos_history = []
    actor.mind.perception.entity_memory = {}
    actor.mind.perception.memory_stale_ticks = {}
    actor.mind.perception.attention_pool = []
    actor.mind.narrative.memory_locations = {}
    
    ctx = MagicMock(actor=actor, config=config)
    ctx.visible = []
    ctx.snapshot.tick = 100
    
    # AI Brain phases
    updates = []
    snapshot = ctx.snapshot
    brain._faction_reg = MagicMock()
    # Mocking Perception.visible_entities as it's called in perception phase
    with patch('src.ai.brain.Perception.visible_entities', return_value=[]):
        brain._sensory_perception_phase(actor, snapshot, updates)
        brain._memory_appraisal_phase(ctx, updates)
        
        from src.actions.base import ProgressionUpdate
        prog_ups = [u for u in updates if isinstance(u, ProgressionUpdate)]
        assert any(u.age_ticks_delta == 1 for u in prog_ups)
        # Death proposed: hp_delta should be -10 (actor.combat.hp)
        assert any(u.hp_delta == -10 for u in prog_ups)
