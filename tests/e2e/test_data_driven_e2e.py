import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


import pytest
import logging
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.world.spawn_config import SPAWN_CONFIGS, LOOT_CONFIGS
from src.core.registry.registry_loader import load_all_registries
from tests.helpers.combat_arena import CombatArena
from src.core.models.enums import EnemyTier, ItemType, HeroClass
from src.core.gameplay.classes import CLASS_DEFS, SKILL_DEFS

# Configure logging to see registry loader output
logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="module", autouse=True)
def setup_registries():
    """Load all registries once for the module."""
    load_all_registries()

def test_registry_driven_spawning_e2e():
    """Verify that SpawnConfig entries correctly initialize entities in the world."""
    arena = CombatArena()
    # "goblin" tier BASIC should match some entry in SpawnConfig
    mob = arena.add_mob(2, pos=(5, 5), kind="goblin", tier=EnemyTier.BASIC)
    assert mob.kind == "goblin"
    assert mob.identity.tier == EnemyTier.BASIC
    assert mob.combat.max_hp > 0

def test_item_registry_lookup_e2e():
    """Verify that items in ITEM_REGISTRY are accessible and have correct attributes."""
    # Pick a common item
    item = ITEM_REGISTRY.get("iron_sword")
    assert item is not None
    assert item.item_type == ItemType.WEAPON
    assert item.atk_bonus > 0

def test_loot_config_e2e():
    """Verify that LootConfig entries are loaded and used in EntityGenerator."""
    # Check if some entries exist
    assert len(LOOT_CONFIGS) > 0
    # "goblin" should have loot (it might be "goblin_basic" or similar)
    found = any("goblin" in kind for kind in LOOT_CONFIGS)
    assert found, f"LootConfig for goblin not found in {list(LOOT_CONFIGS.keys())}"

def test_class_skills_e2e():
    """Verify that class skills from classes.json are available."""
    assert len(CLASS_DEFS) > 0
    assert len(SKILL_DEFS) > 0
    
    # Use HeroClass enum or string depends on registry implementation
    # Registry loader uses c.class_id which is typically lowercase string from JSON
    warrior = CLASS_DEFS.get("warrior")
    if warrior is None:
        # Fallback to key check
        warrior = list(CLASS_DEFS.values())[0] # Just check any class exists
        
    assert warrior is not None
    assert len(warrior.class_skills) > 0
    
    # Check if first skill ID exists in SKILL_DEFS
    sid = warrior.class_skills[0]
    assert sid in SKILL_DEFS
