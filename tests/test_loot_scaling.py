"""Tests for difficulty-based loot scaling (epic-15 Phase C, F4)."""

from __future__ import annotations

import unittest

from src.config import SimulationConfig
from src.core.enums import EnemyTier, Rarity
from src.core.grid import Grid
from src.core.items import (
    CHEST_LOOT_TABLES, DIFFICULTY_BONUS_LOOT, DIFFICULTY_DROP_MULTIPLIER,
    ITEM_REGISTRY,
)
from src.core.models import Vector2
from src.core.world_state import WorldState
from src.systems.generator import EntityGenerator
from src.systems.rng import DeterministicRNG
from src.systems.spatial_hash import SpatialHash


def _make_world(seed: int = 42) -> WorldState:
    cfg = SimulationConfig()
    grid = Grid(cfg.grid_width, cfg.grid_height)
    spatial = SpatialHash(cfg.spatial_cell_size)
    return WorldState(seed=seed, grid=grid, spatial_index=spatial)


def _make_generator(seed: int = 42) -> tuple[EntityGenerator, DeterministicRNG]:
    cfg = SimulationConfig()
    rng = DeterministicRNG(seed)
    return EntityGenerator(cfg, rng), rng


class TestDifficultyDropMultiplier(unittest.TestCase):
    """Test that DIFFICULTY_DROP_MULTIPLIER is defined for all tiers."""

    def test_all_tiers_defined(self):
        for tier in range(1, 5):
            self.assertIn(tier, DIFFICULTY_DROP_MULTIPLIER)

    def test_tier1_is_baseline(self):
        self.assertEqual(DIFFICULTY_DROP_MULTIPLIER[1], 1.0)

    def test_tiers_scale_up(self):
        for tier in range(1, 4):
            self.assertLess(
                DIFFICULTY_DROP_MULTIPLIER[tier],
                DIFFICULTY_DROP_MULTIPLIER[tier + 1],
            )


class TestDifficultyBonusLoot(unittest.TestCase):
    """Test that DIFFICULTY_BONUS_LOOT is defined for all tiers."""

    def test_all_tiers_defined(self):
        for tier in range(1, 5):
            self.assertIn(tier, DIFFICULTY_BONUS_LOOT)

    def test_tier1_empty(self):
        self.assertEqual(len(DIFFICULTY_BONUS_LOOT[1]), 0)

    def test_higher_tiers_have_bonus(self):
        for tier in range(2, 5):
            self.assertGreater(len(DIFFICULTY_BONUS_LOOT[tier]), 0)

    def test_all_bonus_items_exist_in_registry(self):
        for tier, entries in DIFFICULTY_BONUS_LOOT.items():
            for item_id, chance in entries:
                self.assertIn(item_id, ITEM_REGISTRY,
                              f"Bonus item '{item_id}' (tier {tier}) not in registry")
                self.assertGreater(chance, 0.0)
                self.assertLessEqual(chance, 1.0)


class TestChestLootTier4(unittest.TestCase):
    """Test that tier 4 chest loot table exists and contains epic items."""

    def test_tier4_defined(self):
        self.assertIn(4, CHEST_LOOT_TABLES)

    def test_tier4_has_entries(self):
        self.assertGreater(len(CHEST_LOOT_TABLES[4]), 5)

    def test_tier4_items_exist_in_registry(self):
        for item_id, chance, min_c, max_c in CHEST_LOOT_TABLES[4]:
            self.assertIn(item_id, ITEM_REGISTRY,
                          f"Chest item '{item_id}' not in registry")

    def test_tier4_has_epic_items(self):
        epic_items = []
        for item_id, chance, min_c, max_c in CHEST_LOOT_TABLES[4]:
            tmpl = ITEM_REGISTRY.get(item_id)
            if tmpl and tmpl.rarity == Rarity.EPIC:
                epic_items.append(item_id)
        self.assertGreater(len(epic_items), 0,
                           "Tier 4 chest should contain at least one EPIC item")


class TestEpicRarity(unittest.TestCase):
    """Test that EPIC rarity and items exist."""

    def test_epic_rarity_value(self):
        self.assertEqual(Rarity.EPIC, 3)

    def test_epic_items_in_registry(self):
        epic_items = [
            item_id for item_id, tmpl in ITEM_REGISTRY.items()
            if tmpl.rarity == Rarity.EPIC
        ]
        self.assertGreaterEqual(len(epic_items), 5,
                                "Should have at least 5 epic items")


class TestLootScalingInGenerator(unittest.TestCase):
    """Test that higher difficulty produces more loot in entity inventories."""

    def test_tier4_has_more_items_on_average(self):
        """Over many spawns, tier 4 should drop more items than tier 1."""
        total_items_t1 = 0
        total_items_t4 = 0
        n = 20

        for i in range(n):
            gen, _ = _make_generator(seed=1000 + i)
            world = _make_world(seed=1000 + i)
            e = gen.spawn(world, tier=EnemyTier.BASIC, difficulty_tier=1)
            total_items_t1 += len(e.inventory.items) if e.inventory else 0

        for i in range(n):
            gen, _ = _make_generator(seed=1000 + i)
            world = _make_world(seed=1000 + i)
            e = gen.spawn(world, tier=EnemyTier.BASIC, difficulty_tier=4)
            total_items_t4 += len(e.inventory.items) if e.inventory else 0

        self.assertGreater(total_items_t4, total_items_t1,
                           f"Tier 4 total items ({total_items_t4}) should exceed tier 1 ({total_items_t1})")


if __name__ == "__main__":
    unittest.main()
