import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock, patch
from src_legacy.ai.brain import AIBrain
from src_legacy.core.models.enums import AIState, Faction
from src_legacy.core.models import Vector2
from src_legacy.core.entities.entity import Entity

@pytest.fixture
def brain():
    config = MagicMock()
    rng = MagicMock()
    return AIBrain(config, rng)

def test_perception_phase_populates_attention_pool(brain):
    # Setup with REAL Entities [AOA STABILIZATION]
    actor = Entity(id=1, kind="hero", faction=Faction.HERO_GUILD)
    actor.spatial.pos = Vector2(0, 0)
    actor.spatial.vision_range = 10
    actor.mind.perception.max_attention_slots = 3
    actor.mind.perception.attention_pool = []
    
    # Mock entities with REAL Entity objects for distance/salience comparisons
    def make_ent(eid, pos, faction):
        e = Entity(id=eid, kind="creature", faction=faction)
        e.spatial.pos = pos
        e.combat.hp = 100
        e.combat.max_hp = 100
        return e

    # 4 Entities within vision
    e1 = make_ent(101, Vector2(1, 0), Faction.GOBLIN_HORDE)
    e2 = make_ent(102, Vector2(2, 0), Faction.GOBLIN_HORDE)
    e3 = make_ent(103, Vector2(5, 0), Faction.HERO_GUILD)
    e4 = make_ent(104, Vector2(10, 0), Faction.GOBLIN_HORDE)
    
    # Configure faction hostility for salience [AOA STABILIZATION]
    from src_legacy.core.gameplay.faction import FactionRelation
    brain._faction_reg.set_relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE, FactionRelation.HOSTILE)
    
    with patch('src.ai.brain.Perception.visible_entities', return_value=[e1, e2, e3, e4]):
        # Run perception
        updates = []
        snap = MagicMock()
        snap.tick = 100
        snap.social_registry = MagicMock()
        snap.social_registry.get_bond_or_none.return_value = None
        snap.social_registry.get_reputation.return_value = 0
        snap.group_registry = {}
        brain._sensory_perception_phase(actor, snap, updates)
        
        # Check updates instead of actor (AOA is pure)
        from src_legacy.actions.base import PerceptionUpdate
        p_up = next(u for u in updates if isinstance(u, PerceptionUpdate))
        assert len(p_up.attention_pool) == 3
        # e3 (Hero) should be EXCLUDED if salience is lower, or e4 if e3 is priority.
        # Actually salience = weight / (dist + 1). 
        # e1: 2.0 / (1+1) = 1.0
        # e2: 2.0 / (2+1) = 0.66
        # e3: 1.0 / (5+1) = 0.16
        # e4: 2.0 / (10+1) = 0.18
        # Pool (3 slots): [e1, e2, e4] -> e3 excluded.
        assert 103 not in p_up.attention_pool
            
        # Highly salient entities (hostile and close) should be first (e1, e2)
        assert 101 in p_up.attention_pool
        assert 102 in p_up.attention_pool
