"""Tests for region enter/leave events and AI difficulty awareness (epic-15 Phase C+D)."""

from __future__ import annotations

import unittest

from src.ai.goals.scorers import (
    _current_region_difficulty,
    _region_danger_penalty,
)
from src.ai.states import AIContext
from src.config import SimulationConfig
from src.core.enums import Material
from src.core.faction import Faction, FactionRegistry
from src.core.grid import Grid
from src.core.models import Entity, Stats, Vector2
from src.core.regions import Region
from src.core.snapshot import Snapshot
from src.core.world_state import WorldState
from src.systems.rng import DeterministicRNG
from src.systems.spatial_hash import SpatialHash


def _make_world(seed: int = 42) -> WorldState:
    cfg = SimulationConfig()
    grid = Grid(cfg.grid_width, cfg.grid_height)
    spatial = SpatialHash(cfg.spatial_cell_size)
    return WorldState(seed=seed, grid=grid, spatial_index=spatial)


def _make_hero(eid: int = 1, level: int = 1, pos: Vector2 = None) -> Entity:
    if pos is None:
        pos = Vector2(50, 50)
    return Entity(
        id=eid, kind="hero", pos=pos,
        stats=Stats(level=level, hp=100, max_hp=100),
        faction=Faction.HERO_GUILD,
    )


def _make_ctx(hero: Entity, regions: list[Region] | None = None) -> AIContext:
    world = _make_world()
    if regions:
        world.regions = regions
    world.add_entity(hero)
    snap = Snapshot.from_world(world)
    cfg = SimulationConfig()
    rng = DeterministicRNG(42)
    return AIContext(
        actor=hero,
        snapshot=snap,
        config=cfg,
        rng=rng,
        faction_reg=FactionRegistry.default(),
    )


class TestCurrentRegionDifficulty(unittest.TestCase):
    """Test _current_region_difficulty helper."""

    def test_no_region_returns_0(self):
        hero = _make_hero()
        ctx = _make_ctx(hero)
        self.assertEqual(_current_region_difficulty(ctx), 0)

    def test_in_region_returns_difficulty(self):
        hero = _make_hero(pos=Vector2(50, 50))
        hero.current_region_id = "test_region"
        region = Region(
            region_id="test_region", name="Test", terrain=Material.FOREST,
            center=Vector2(50, 50), radius=20, difficulty=3,
        )
        ctx = _make_ctx(hero, regions=[region])
        self.assertEqual(_current_region_difficulty(ctx), 3)

    def test_unknown_region_returns_0(self):
        hero = _make_hero()
        hero.current_region_id = "nonexistent"
        ctx = _make_ctx(hero)
        self.assertEqual(_current_region_difficulty(ctx), 0)


class TestRegionDangerPenalty(unittest.TestCase):
    """Test _region_danger_penalty helper."""

    def test_no_region_no_penalty(self):
        hero = _make_hero(level=1)
        ctx = _make_ctx(hero)
        self.assertEqual(_region_danger_penalty(ctx), 0.0)

    def test_safe_region_no_penalty(self):
        """Level 5 hero in tier 1 region: 1*3=3 <= 5+3=8, no penalty."""
        hero = _make_hero(level=5, pos=Vector2(50, 50))
        hero.current_region_id = "safe"
        region = Region(
            region_id="safe", name="Safe", terrain=Material.FOREST,
            center=Vector2(50, 50), radius=20, difficulty=1,
        )
        ctx = _make_ctx(hero, regions=[region])
        self.assertEqual(_region_danger_penalty(ctx), 0.0)

    def test_dangerous_region_has_penalty(self):
        """Level 1 hero in tier 4 region: 4*3=12 > 1+3=4, excess=8, penalty=0.4 (capped)."""
        hero = _make_hero(level=1, pos=Vector2(50, 50))
        hero.current_region_id = "deadly"
        region = Region(
            region_id="deadly", name="Deadly", terrain=Material.MOUNTAIN,
            center=Vector2(50, 50), radius=20, difficulty=4,
        )
        ctx = _make_ctx(hero, regions=[region])
        penalty = _region_danger_penalty(ctx)
        self.assertGreater(penalty, 0.0)
        self.assertLessEqual(penalty, 0.4)

    def test_marginal_danger(self):
        """Level 3 hero in tier 3 region: 3*3=9 > 3+3=6, excess=3, penalty=0.15."""
        hero = _make_hero(level=3, pos=Vector2(50, 50))
        hero.current_region_id = "wilds"
        region = Region(
            region_id="wilds", name="Wilds", terrain=Material.SWAMP,
            center=Vector2(50, 50), radius=20, difficulty=3,
        )
        ctx = _make_ctx(hero, regions=[region])
        penalty = _region_danger_penalty(ctx)
        self.assertAlmostEqual(penalty, 0.15)


class TestRegionTrackingOnEntity(unittest.TestCase):
    """Test that current_region_id field exists and works."""

    def test_default_empty(self):
        hero = _make_hero()
        self.assertEqual(hero.current_region_id, "")

    def test_settable(self):
        hero = _make_hero()
        hero.current_region_id = "whispering_woods"
        self.assertEqual(hero.current_region_id, "whispering_woods")


class TestRegionContains(unittest.TestCase):
    """Test Region.contains for transition logic."""

    def test_inside(self):
        r = Region(
            region_id="r1", name="R1", terrain=Material.FOREST,
            center=Vector2(50, 50), radius=10, difficulty=1,
        )
        self.assertTrue(r.contains(Vector2(55, 53)))

    def test_outside(self):
        r = Region(
            region_id="r1", name="R1", terrain=Material.FOREST,
            center=Vector2(50, 50), radius=10, difficulty=1,
        )
        self.assertFalse(r.contains(Vector2(70, 70)))

    def test_boundary(self):
        r = Region(
            region_id="r1", name="R1", terrain=Material.FOREST,
            center=Vector2(50, 50), radius=10, difficulty=1,
        )
        # Manhattan distance = 10, should be inside (radius inclusive)
        self.assertTrue(r.contains(Vector2(60, 50)))


if __name__ == "__main__":
    unittest.main()
