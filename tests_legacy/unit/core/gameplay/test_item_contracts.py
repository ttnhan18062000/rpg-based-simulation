import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

"""Data-integrity contract tests for the Item Registry."""

import pytest
from src_legacy.core.gameplay.items.item_registry import ITEM_REGISTRY

# Verifying that the dynamic loading from items.json resulted in the expected contract.
# This replaces the 10+ legacy individual weapon tests with a clean parametrized suite.
@pytest.mark.parametrize("item_id, expected_range", [
    ("wooden_club", 1),
    ("iron_sword", 1),
    ("steel_sword", 1),
    ("battle_axe", 1),
    ("enchanted_blade", 1),
    ("goblin_cleaver", 1),
    ("shortbow", 3),
    ("longbow", 4),
    ("hunting_bow", 4),
    ("windpiercer", 5),
    ("stormcaller", 4),
    ("apprentice_staff", 3),
    ("crystal_staff", 4),
    ("bandit_dagger", 1),
    ("bandit_bow", 3),
    ("orc_axe", 1),
    ("steel_greatsword", 1),
])
def test_weapon_ranges_integrity(item_id, expected_range):
    """Verify that specific weapons have their intended ranges in the registry."""
    item = ITEM_REGISTRY.get(item_id)
    assert item is not None, f"Item {item_id} missing from registry"
    assert item.weapon_range == expected_range, f"{item_id} should have range {expected_range}, got {item.weapon_range}"

@pytest.mark.parametrize("item_id, expected_power, attr", [
    ("iron_sword", 4, "atk_bonus"),
    ("steel_sword", 6, "atk_bonus"),
    ("windpiercer", 13, "atk_bonus"),
    ("stormcaller", 15, "matk_bonus"),
    ("goblin_cleaver", 12, "atk_bonus"),
])
def test_weapon_power_integrity(item_id, expected_power, attr):
    """Verify that core progression weapons have their primary power correctly set."""
    item = ITEM_REGISTRY.get(item_id)
    assert item is not None
    assert getattr(item, attr) == expected_power

@pytest.mark.parametrize("item_id", [
    "leather_vest", "chainmail", "iron_plate", "enchanted_robe", "goblin_guard",
    "wood", "iron_ore", "steel_bar", "leather", "enchanted_dust",
    "herb", "wild_berries", "raw_gem", "fiber", "glowing_mushroom"
])
def test_registry_identity_integrity(item_id):
    """Ensure all core items are successfully loaded and have consistent IDs."""
    item = ITEM_REGISTRY.get(item_id)
    assert item is not None
    assert item.item_id == item_id
