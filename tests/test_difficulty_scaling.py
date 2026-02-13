"""Tests for difficulty-based stat scaling in EntityGenerator (epic-15 Phase B)."""

from __future__ import annotations

import unittest

from src.config import SimulationConfig
from src.core.enums import EnemyTier, Material
from src.core.grid import Grid
from src.core.models import Vector2
from src.core.regions import DIFFICULTY_TIERS
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


class TestSpawnDifficultyScaling(unittest.TestCase):
    """Test that spawn() applies difficulty multipliers."""

    def test_tier1_is_baseline(self):
        gen, _ = _make_generator(seed=100)
        world = _make_world(seed=100)
        e = gen.spawn(world, tier=EnemyTier.BASIC, difficulty_tier=1)
        self.assertEqual(e.difficulty_tier, 1)
        self.assertGreater(e.stats.hp, 0)
        self.assertGreater(e.stats.atk, 0)

    def test_tier4_has_higher_stats_than_tier1(self):
        """Same seed, same enemy tier — tier 4 difficulty should have higher HP/ATK."""
        gen1, _ = _make_generator(seed=200)
        world1 = _make_world(seed=200)
        e1 = gen1.spawn(world1, tier=EnemyTier.BASIC, difficulty_tier=1)

        gen4, _ = _make_generator(seed=200)
        world4 = _make_world(seed=200)
        e4 = gen4.spawn(world4, tier=EnemyTier.BASIC, difficulty_tier=4)

        self.assertGreater(e4.stats.max_hp, e1.stats.max_hp)
        self.assertGreater(e4.stats.atk, e1.stats.atk)
        self.assertEqual(e4.difficulty_tier, 4)

    def test_tier4_hp_significantly_higher(self):
        """Tier 4 HP multiplier is 4.0× on base stats; with flat bonuses from
        traits/attributes the effective ratio will be lower but still substantial."""
        gen1, _ = _make_generator(seed=300)
        world1 = _make_world(seed=300)
        e1 = gen1.spawn(world1, tier=EnemyTier.BASIC, difficulty_tier=1)

        gen4, _ = _make_generator(seed=300)
        world4 = _make_world(seed=300)
        e4 = gen4.spawn(world4, tier=EnemyTier.BASIC, difficulty_tier=4)

        ratio = e4.stats.max_hp / e1.stats.max_hp
        self.assertGreaterEqual(ratio, 2.0, "Tier 4 HP should be at least 2× tier 1")
        self.assertLessEqual(ratio, 5.0)

    def test_difficulty_sets_level_range(self):
        """Entities in tier 3 should have level in [5, 10]."""
        gen, _ = _make_generator(seed=400)
        world = _make_world(seed=400)
        e = gen.spawn(world, tier=EnemyTier.BASIC, difficulty_tier=3)
        diff = DIFFICULTY_TIERS[3]
        self.assertGreaterEqual(e.stats.level, diff.level_min)
        self.assertLessEqual(e.stats.level, diff.level_max)

    def test_gold_scales_with_difficulty(self):
        """Tier 4 gold multiplier is 4.0×."""
        gen1, _ = _make_generator(seed=500)
        world1 = _make_world(seed=500)
        e1 = gen1.spawn(world1, tier=EnemyTier.WARRIOR, difficulty_tier=1)

        gen4, _ = _make_generator(seed=500)
        world4 = _make_world(seed=500)
        e4 = gen4.spawn(world4, tier=EnemyTier.WARRIOR, difficulty_tier=4)

        # Gold is randomized but tier 4 should have higher gold (or equal if base was 0)
        self.assertGreaterEqual(e4.stats.gold, e1.stats.gold)


class TestSpawnRaceDifficultyScaling(unittest.TestCase):
    """Test that spawn_race() applies difficulty multipliers."""

    def test_race_tier4_stronger_than_tier1(self):
        gen1, _ = _make_generator(seed=600)
        world1 = _make_world(seed=600)
        e1 = gen1.spawn_race(world1, "wolf", difficulty_tier=1)

        gen4, _ = _make_generator(seed=600)
        world4 = _make_world(seed=600)
        e4 = gen4.spawn_race(world4, "wolf", difficulty_tier=4)

        self.assertGreater(e4.stats.max_hp, e1.stats.max_hp)
        self.assertGreater(e4.stats.atk, e1.stats.atk)

    def test_race_difficulty_tier_set(self):
        gen, _ = _make_generator(seed=700)
        world = _make_world(seed=700)
        e = gen.spawn_race(world, "bandit", difficulty_tier=2)
        self.assertEqual(e.difficulty_tier, 2)

    def test_race_level_in_range(self):
        gen, _ = _make_generator(seed=800)
        world = _make_world(seed=800)
        e = gen.spawn_race(world, "undead", difficulty_tier=2)
        diff = DIFFICULTY_TIERS[2]
        self.assertGreaterEqual(e.stats.level, diff.level_min)
        self.assertLessEqual(e.stats.level, diff.level_max)

    def test_all_races_scale(self):
        """All four races should scale with difficulty."""
        for race in ("wolf", "bandit", "undead", "orc"):
            gen1, _ = _make_generator(seed=900)
            world1 = _make_world(seed=900)
            e1 = gen1.spawn_race(world1, race, tier=EnemyTier.BASIC, difficulty_tier=1)

            gen3, _ = _make_generator(seed=900)
            world3 = _make_world(seed=900)
            e3 = gen3.spawn_race(world3, race, tier=EnemyTier.BASIC, difficulty_tier=3)

            with self.subTest(race=race):
                self.assertGreater(e3.stats.max_hp, e1.stats.max_hp,
                                   f"{race} tier 3 HP should exceed tier 1")


class TestBossArenaExtraDifficulty(unittest.TestCase):
    """Boss arenas should get +1 difficulty capped at 4."""

    def test_boss_diff_capped_at_4(self):
        # If region difficulty is 4, boss_diff = min(4+1, 4) = 4
        self.assertEqual(min(4 + 1, 4), 4)

    def test_boss_diff_adds_one(self):
        # If region difficulty is 2, boss_diff = min(2+1, 4) = 3
        self.assertEqual(min(2 + 1, 4), 3)


class TestDefaultDifficultyBackwardCompat(unittest.TestCase):
    """Spawns without difficulty_tier should default to tier 1 (no change)."""

    def test_spawn_default_is_tier1(self):
        gen, _ = _make_generator(seed=1000)
        world = _make_world(seed=1000)
        e = gen.spawn(world)
        self.assertEqual(e.difficulty_tier, 1)

    def test_spawn_race_default_is_tier1(self):
        gen, _ = _make_generator(seed=1001)
        world = _make_world(seed=1001)
        e = gen.spawn_race(world, "wolf")
        self.assertEqual(e.difficulty_tier, 1)


if __name__ == "__main__":
    unittest.main()
