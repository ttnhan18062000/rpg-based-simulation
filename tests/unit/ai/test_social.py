import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from unittest.mock import MagicMock, patch
from src.systems.lifecycle.hero_lifecycle_system import HeroLifecycleSystem
from src.systems.infrastructure.base import SystemContext
from src.core.models.vectors import Vector2
from src.core.models.enums import AIState, ItemType
from src.core.aspects.mind import MemoryRecord

class MockRNG:
    def __init__(self):
        self.float_val = 0.1
        self.int_vals = [0, 1, 0, 1] # Sequence of indices
        self.int_idx = 0
        
    def next_float(self, *args): return self.float_val
    def next_int(self, domain, actor_id, tick, min_val, max_val):
        val = self.int_vals[self.int_idx % len(self.int_vals)]
        self.int_idx += 1
        return val

@pytest.fixture
def system():
    return HeroLifecycleSystem(config=MagicMock(), rng=MockRNG())

@pytest.fixture
def context():
    ctx = MagicMock(spec=SystemContext)
    ctx.world = MagicMock()
    ctx.world.entities = {}
    ctx.emit = MagicMock()
    return ctx

def test_inn_gossip(system, context):
    # Setup two heroes at the same position in VISIT_INN state
    h1 = MagicMock()
    h1.id = 1
    h1.spatial.pos = Vector2(10, 10)
    h1.kind = "hero"
    h1.combat.alive = True
    h1.mind.decision.ai_state = AIState.VISIT_INN
    h1.identity.display_name = "Hero1"
    
    mem = MemoryRecord(entity_id=99, pos=Vector2(50, 50), kind="boss")
    h1.mind.perception.entity_memory = {99: mem}
    
    h2 = MagicMock()
    h2.id = 2
    h2.spatial.pos = Vector2(10, 10)
    h2.kind = "hero"
    h2.combat.alive = True
    h2.mind.decision.ai_state = AIState.VISIT_INN
    h2.identity.display_name = "Hero2"
    h2.mind.perception.entity_memory = {}
    
    context.world.entities = {1: h1, 2: h2}
    
    system._tick_inn_gossip(context, 100)
    
    assert 99 in h2.mind.perception.entity_memory
    assert h2.mind.perception.entity_memory[99].entity_id == 99
    context.emit.assert_called()

def test_hero_trading(system, context):
    # Setup two heroes at the same position
    h1 = MagicMock()
    h1.id = 1
    h1.spatial.pos = Vector2(10, 10)
    h1.kind = "hero"
    h1.combat.alive = True
    h1.mind.decision.ai_state = AIState.VISIT_INN
    h1.identity.display_name = "Donor"
    h1.inventory.items = ["iron_sword"] # Spare item
    h1.inventory.equipped = {ItemType.WEAPON: "steel_sword"} # Donor has better
    h1.inventory.can_add.return_value = True
    
    h2 = MagicMock()
    h2.id = 2
    h2.spatial.pos = Vector2(10, 10)
    h2.kind = "hero"
    h2.combat.alive = True
    h2.mind.decision.ai_state = AIState.VISIT_INN
    h2.identity.display_name = "Recipient"
    h2.inventory.items = []
    h2.inventory.equipped = {} # Recipient has nothing
    h2.inventory.can_add.return_value = True
    
    context.world.entities = {1: h1, 2: h2}
    
    with patch("src.core.gameplay.items.item_registry.ITEM_REGISTRY") as mock_reg:
        iron_t = MagicMock()
        iron_t.item_type = ItemType.WEAPON
        iron_t.atk_bonus = 10; iron_t.def_bonus = 0; iron_t.matk_bonus = 0; iron_t.mdef_bonus = 0
        iron_t.max_hp_bonus = 0; iron_t.crit_rate_bonus = 0.0; iron_t.evasion_bonus = 0.0
        iron_t.name = "Iron Sword"
        
        steel_t = MagicMock()
        steel_t.item_type = ItemType.WEAPON
        steel_t.atk_bonus = 20; steel_t.def_bonus = 0; steel_t.matk_bonus = 0; steel_t.mdef_bonus = 0
        steel_t.max_hp_bonus = 0; steel_t.crit_rate_bonus = 0.0; steel_t.evasion_bonus = 0.0
        steel_t.name = "Steel Sword"
        
        mock_reg.get.side_effect = lambda iid: iron_t if iid == "iron_sword" else steel_t
        
        system._tick_hero_trading(context, 100)
        
    h1.inventory.remove_item.assert_called_with("iron_sword")
    h2.inventory.add_item.assert_called_with("iron_sword")
    context.emit.assert_called()
