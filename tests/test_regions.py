"""Tests for the Region & Location data model and generation (epic-15)."""

from __future__ import annotations

import unittest

from src.config import SimulationConfig
from src.core.enums import Material
from src.core.models import Vector2
from src.core.regions import (
    DIFFICULTY_TIERS,
    LOCATION_NAME_TEMPLATES,
    LOCATION_TYPES,
    REGION_NAMES,
    TERRAIN_RACE_LABEL,
    DifficultyMultipliers,
    Location,
    Region,
    difficulty_for_distance,
    pick_region_name,
    reset_name_counters,
)


class TestRegionDataclass(unittest.TestCase):
    """Basic Region/Location dataclass tests."""

    def test_region_creation(self):
        r = Region(
            region_id="test_forest",
            name="Test Forest",
            terrain=Material.FOREST,
            center=Vector2(50, 50),
            radius=20,
            difficulty=2,
        )
        self.assertEqual(r.region_id, "test_forest")
        self.assertEqual(r.name, "Test Forest")
        self.assertEqual(r.terrain, Material.FOREST)
        self.assertEqual(r.radius, 20)
        self.assertEqual(r.difficulty, 2)
        self.assertEqual(r.locations, [])

    def test_region_contains(self):
        r = Region(
            region_id="r1", name="R1", terrain=Material.FOREST,
            center=Vector2(50, 50), radius=10, difficulty=1,
        )
        self.assertTrue(r.contains(Vector2(50, 50)))
        self.assertTrue(r.contains(Vector2(55, 55)))  # manhattan 10
        self.assertFalse(r.contains(Vector2(56, 56)))  # manhattan 12

    def test_region_copy(self):
        loc = Location(
            location_id="loc1", name="Camp", location_type="enemy_camp",
            pos=Vector2(52, 53), region_id="r1",
        )
        r = Region(
            region_id="r1", name="R1", terrain=Material.DESERT,
            center=Vector2(50, 50), radius=15, difficulty=3,
            locations=[loc],
        )
        c = r.copy()
        self.assertEqual(c.region_id, r.region_id)
        self.assertEqual(len(c.locations), 1)
        self.assertEqual(c.locations[0].name, "Camp")
        # Verify it's a deep copy
        c.locations[0].name = "Changed"
        self.assertEqual(r.locations[0].name, "Camp")

    def test_location_creation(self):
        loc = Location(
            location_id="loc1", name="Wolf Outpost",
            location_type="enemy_camp", pos=Vector2(10, 20), region_id="r1",
        )
        self.assertEqual(loc.location_id, "loc1")
        self.assertEqual(loc.location_type, "enemy_camp")
        self.assertEqual(loc.pos.x, 10)


class TestDifficultyZones(unittest.TestCase):
    """Test difficulty_for_distance function."""

    def test_tier_1_close(self):
        zones = [(35, 1), (60, 2), (90, 3), (999, 4)]
        self.assertEqual(difficulty_for_distance(20, zones), 1)

    def test_tier_2_medium(self):
        zones = [(35, 1), (60, 2), (90, 3), (999, 4)]
        self.assertEqual(difficulty_for_distance(50, zones), 2)

    def test_tier_3_far(self):
        zones = [(35, 1), (60, 2), (90, 3), (999, 4)]
        self.assertEqual(difficulty_for_distance(80, zones), 3)

    def test_tier_4_distant(self):
        zones = [(35, 1), (60, 2), (90, 3), (999, 4)]
        self.assertEqual(difficulty_for_distance(100, zones), 4)

    def test_boundary_exact(self):
        zones = [(35, 1), (60, 2), (90, 3), (999, 4)]
        self.assertEqual(difficulty_for_distance(35, zones), 1)
        self.assertEqual(difficulty_for_distance(60, zones), 2)

    def test_empty_zones_returns_1(self):
        self.assertEqual(difficulty_for_distance(50, []), 1)


class TestRegionNames(unittest.TestCase):
    """Test region name picking and counters."""

    def setUp(self):
        reset_name_counters()

    def test_pick_returns_string(self):
        name = pick_region_name(Material.FOREST)
        self.assertIsInstance(name, str)
        self.assertGreater(len(name), 0)

    def test_sequential_names_differ(self):
        n1 = pick_region_name(Material.DESERT)
        n2 = pick_region_name(Material.DESERT)
        self.assertNotEqual(n1, n2)

    def test_reset_restarts_sequence(self):
        n1 = pick_region_name(Material.SWAMP)
        reset_name_counters()
        n2 = pick_region_name(Material.SWAMP)
        self.assertEqual(n1, n2)

    def test_all_terrains_have_names(self):
        for mat in (Material.FOREST, Material.DESERT, Material.SWAMP, Material.MOUNTAIN):
            self.assertIn(int(mat), REGION_NAMES)
            self.assertGreater(len(REGION_NAMES[int(mat)]), 0)

    def test_all_terrains_have_race_labels(self):
        for mat in (Material.FOREST, Material.DESERT, Material.SWAMP, Material.MOUNTAIN):
            self.assertIn(int(mat), TERRAIN_RACE_LABEL)


class TestDifficultyTiers(unittest.TestCase):
    """Test difficulty multiplier tables."""

    def test_all_tiers_defined(self):
        for tier in range(1, 5):
            self.assertIn(tier, DIFFICULTY_TIERS)

    def test_tiers_scale_up(self):
        for tier in range(1, 4):
            lower = DIFFICULTY_TIERS[tier]
            upper = DIFFICULTY_TIERS[tier + 1]
            self.assertGreater(upper.hp, lower.hp)
            self.assertGreater(upper.atk, lower.atk)
            self.assertGreater(upper.xp, lower.xp)

    def test_tier_1_is_baseline(self):
        t = DIFFICULTY_TIERS[1]
        self.assertEqual(t.hp, 1.0)
        self.assertEqual(t.atk, 1.0)
        self.assertEqual(t.def_, 1.0)


class TestLocationTypes(unittest.TestCase):
    """Test location type constants."""

    def test_all_types_have_name_templates(self):
        for lt in LOCATION_TYPES:
            self.assertIn(lt, LOCATION_NAME_TEMPLATES, f"Missing template for {lt}")
            self.assertGreater(len(LOCATION_NAME_TEMPLATES[lt]), 0)

    def test_expected_types_present(self):
        expected = {
            "enemy_camp", "resource_grove", "ruins", "dungeon_entrance", "shrine", "boss_arena",
            "outpost", "watchtower", "portal", "fishing_spot", "graveyard", "obelisk",
        }
        self.assertEqual(set(LOCATION_TYPES), expected)


class TestConfigDefaults(unittest.TestCase):
    """Test that config has the new region parameters."""

    def test_map_512(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.grid_width, 512)
        self.assertEqual(cfg.grid_height, 512)

    def test_region_counts(self):
        cfg = SimulationConfig()
        self.assertEqual(cfg.num_forest_regions, 4)
        self.assertEqual(cfg.num_desert_regions, 3)
        self.assertEqual(cfg.num_swamp_regions, 3)
        self.assertEqual(cfg.num_mountain_regions, 3)
        self.assertEqual(cfg.num_grassland_regions, 4)
        self.assertEqual(cfg.num_snow_regions, 3)
        self.assertEqual(cfg.num_jungle_regions, 3)
        self.assertEqual(cfg.num_volcanic_regions, 2)

    def test_region_radius_range(self):
        cfg = SimulationConfig()
        self.assertGreaterEqual(cfg.region_min_radius, 30)
        self.assertLessEqual(cfg.region_max_radius, 60)

    def test_difficulty_zones_defined(self):
        cfg = SimulationConfig()
        self.assertEqual(len(cfg.difficulty_zones), 4)

    def test_location_params(self):
        cfg = SimulationConfig()
        self.assertGreaterEqual(cfg.min_locations_per_region, 3)
        self.assertLessEqual(cfg.max_locations_per_region, 6)


class TestEntityRegionFields(unittest.TestCase):
    """Test that Entity has region_id and difficulty_tier fields."""

    def test_default_region_id(self):
        from src.core.models import Entity, Stats
        e = Entity(id=1, kind="test", pos=Vector2(0, 0), stats=Stats())
        self.assertEqual(e.region_id, "")
        self.assertEqual(e.difficulty_tier, 1)

    def test_region_id_settable(self):
        from src.core.models import Entity, Stats
        e = Entity(id=1, kind="test", pos=Vector2(0, 0), stats=Stats())
        e.region_id = "whispering_woods"
        e.difficulty_tier = 3
        self.assertEqual(e.region_id, "whispering_woods")
        self.assertEqual(e.difficulty_tier, 3)


class TestWorldStateRegions(unittest.TestCase):
    """Test that WorldState holds regions."""

    def test_world_has_regions_list(self):
        from src.core.grid import Grid
        from src.core.world_state import WorldState
        from src.systems.spatial_hash import SpatialHash
        grid = Grid(32, 32)
        spatial = SpatialHash(8)
        world = WorldState(seed=42, grid=grid, spatial_index=spatial)
        self.assertIsInstance(world.regions, list)
        self.assertEqual(len(world.regions), 0)

    def test_add_region(self):
        from src.core.grid import Grid
        from src.core.world_state import WorldState
        from src.systems.spatial_hash import SpatialHash
        grid = Grid(32, 32)
        spatial = SpatialHash(8)
        world = WorldState(seed=42, grid=grid, spatial_index=spatial)
        r = Region(
            region_id="test", name="Test", terrain=Material.FOREST,
            center=Vector2(16, 16), radius=10, difficulty=1,
        )
        world.regions.append(r)
        self.assertEqual(len(world.regions), 1)


class TestSnapshotRegions(unittest.TestCase):
    """Test that Snapshot includes regions."""

    def test_snapshot_contains_regions(self):
        from src.core.grid import Grid
        from src.core.snapshot import Snapshot
        from src.core.world_state import WorldState
        from src.systems.spatial_hash import SpatialHash
        grid = Grid(32, 32)
        spatial = SpatialHash(8)
        world = WorldState(seed=42, grid=grid, spatial_index=spatial)
        r = Region(
            region_id="test", name="Test", terrain=Material.MOUNTAIN,
            center=Vector2(10, 10), radius=8, difficulty=2,
            locations=[Location(
                location_id="loc1", name="Camp",
                location_type="enemy_camp", pos=Vector2(12, 12), region_id="test",
            )],
        )
        world.regions.append(r)
        snap = Snapshot.from_world(world)
        self.assertEqual(len(snap.regions), 1)
        self.assertEqual(snap.regions[0].name, "Test")
        self.assertEqual(len(snap.regions[0].locations), 1)
        # Verify deep copy
        self.assertIsNot(snap.regions[0], r)


if __name__ == "__main__":
    unittest.main()
