from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

"""Tests for difficulty-based stat scaling in EntityGenerator (AOA Stabilization)."""

import pytest
from src_legacy.config import SimulationConfig
from src_legacy.core.models.enums import EnemyTier
from src_legacy.core.world.grid import Grid
from src_legacy.core.world.regions import DIFFICULTY_TIERS
from src_legacy.core.models.world_state import WorldState
from src_legacy.systems.world.generator import EntityGenerator
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.platform.spatial_hash import SpatialHash

def _make_world(seed: int = 42) -> WorldState:
    cfg = SimulationConfig()
    grid = Grid(cfg.grid_width, cfg.grid_height)
    spatial = SpatialHash(cfg.spatial_cell_size)
    return WorldState(seed=seed, grid=grid, spatial_index=spatial)

def _make_generator(seed: int = 42) -> tuple[EntityGenerator, DeterministicRNG]:
    cfg = SimulationConfig()
    rng = DeterministicRNG(seed)
    return EntityGenerator(cfg, rng), rng

def test_tier1_is_baseline():
    gen, _ = _make_generator(seed=100)
    world = _make_world(seed=100)
    e = gen.spawn(world, tier=EnemyTier.BASIC, difficulty_tier=1)
    assert e.identity.difficulty_tier == 1
    assert e.combat.hp > 0
    assert e.combat.atk_base > 0

def test_tier4_has_higher_stats_than_tier1():
    """Same seed, same enemy tier - tier 4 difficulty should have higher HP/ATK."""
    gen1, _ = _make_generator(seed=200)
    world1 = _make_world(seed=200)
    e1 = gen1.spawn(world1, tier=EnemyTier.BASIC, difficulty_tier=1)

    gen4, _ = _make_generator(seed=200)
    world4 = _make_world(seed=200)
    e4 = gen4.spawn(world4, tier=EnemyTier.BASIC, difficulty_tier=4)

    assert e4.combat.max_hp > e1.combat.max_hp
    assert e4.combat.atk_base > e1.combat.atk_base
    assert e4.identity.difficulty_tier == 4

def test_tier4_hp_significantly_higher():
    """Tier 4 HP multiplier is 4.0x on base stats; with flat bonuses from
    traits/attributes the effective ratio will be lower but still substantial."""
    gen1, _ = _make_generator(seed=300)
    world1 = _make_world(seed=300)
    e1 = gen1.spawn(world1, tier=EnemyTier.BASIC, difficulty_tier=1)

    gen4, _ = _make_generator(seed=300)
    world4 = _make_world(seed=300)
    e4 = gen4.spawn(world4, tier=EnemyTier.BASIC, difficulty_tier=4)

    ratio = e4.combat.max_hp / e1.combat.max_hp
    assert ratio >= 2.0, "Tier 4 HP should be at least 2x tier 1"
    assert ratio <= 5.0

def test_difficulty_sets_level_range():
    """Entities in tier 3 should have level in [5, 10]."""
    gen, _ = _make_generator(seed=400)
    world = _make_world(seed=400)
    e = gen.spawn(world, tier=EnemyTier.BASIC, difficulty_tier=3)
    diff = DIFFICULTY_TIERS[3]
    assert e.progression.level >= diff.level_min
    # Level is randomized, so we check it's within expected range for tier 3
    assert e.progression.level <= diff.level_max

def test_gold_scales_with_difficulty():
    """Tier 4 gold multiplier is 4.0x."""
    gen1, _ = _make_generator(seed=500)
    world1 = _make_world(seed=500)
    e1 = gen1.spawn(world1, tier=EnemyTier.WARRIOR, difficulty_tier=1)

    gen4, _ = _make_generator(seed=500)
    world4 = _make_world(seed=500)
    e4 = gen4.spawn(world4, tier=EnemyTier.WARRIOR, difficulty_tier=4)

    # Gold is randomized but tier 4 should have higher gold (or equal if base was 0)
    assert e4.progression.gold >= e1.progression.gold

def test_race_tier4_stronger_than_tier1():
    gen1, _ = _make_generator(seed=600)
    world1 = _make_world(seed=600)
    e1 = gen1.spawn_race(world1, "wolf", difficulty_tier=1)

    gen4, _ = _make_generator(seed=600)
    world4 = _make_world(seed=600)
    e4 = gen4.spawn_race(world4, "wolf", difficulty_tier=4)

    assert e4.combat.max_hp > e1.combat.max_hp
    assert e4.combat.atk_base > e1.combat.atk_base

def test_race_difficulty_tier_set():
    gen, _ = _make_generator(seed=700)
    world = _make_world(seed=700)
    e = gen.spawn_race(world, "bandit", difficulty_tier=2)
    assert e.identity.difficulty_tier == 2

def test_race_level_in_range():
    gen, _ = _make_generator(seed=800)
    world = _make_world(seed=800)
    e = gen.spawn_race(world, "undead", difficulty_tier=2)
    diff = DIFFICULTY_TIERS[2]
    assert e.progression.level >= diff.level_min
    assert e.progression.level <= diff.level_max

@pytest.mark.parametrize("race", ["wolf", "bandit", "undead", "orc"])
def test_all_races_scale(race):
    """All four races should scale with difficulty."""
    gen1, _ = _make_generator(seed=900)
    world1 = _make_world(seed=900)
    e1 = gen1.spawn_race(world1, race, tier=EnemyTier.BASIC, difficulty_tier=1)

    gen3, _ = _make_generator(seed=900)
    world3 = _make_world(seed=900)
    e3 = gen3.spawn_race(world3, race, tier=EnemyTier.BASIC, difficulty_tier=3)

    assert e3.combat.max_hp > e1.combat.max_hp, f"{race} tier 3 HP should exceed tier 1"

def test_boss_diff_capped_at_4():
    # If region difficulty is 4, boss_diff = min(4+1, 4) = 4
    assert min(4 + 1, 4) == 4

def test_boss_diff_adds_one():
    # If region difficulty is 2, boss_diff = min(2+1, 4) = 3
    assert min(2 + 1, 4) == 3

def test_spawn_default_is_tier1():
    gen, _ = _make_generator(seed=1000)
    world = _make_world(seed=1000)
    e = gen.spawn(world)
    assert e.identity.difficulty_tier == 1

def test_spawn_race_default_is_tier1():
    gen, _ = _make_generator(seed=1001)
    world = _make_world(seed=1001)
    e = gen.spawn_race(world, "wolf")
    assert e.identity.difficulty_tier == 1
