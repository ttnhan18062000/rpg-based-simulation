"""Tests for Voronoi region tessellation — regions border each other with no gaps."""

from __future__ import annotations

import unittest

from src.api.engine_manager import EngineManager
from src.config import SimulationConfig
from src.core.enums import Material
from src.core.models import Vector2
from src.core.regions import Region, find_region_at


TOWN_TILES = frozenset({Material.TOWN, Material.SANCTUARY})
# Tiles that are painted over region terrain for specific locations
OVERLAY_TILES = frozenset({Material.CAMP, Material.RUINS, Material.DUNGEON_ENTRANCE, Material.ROAD})
TERRAIN_TILES = frozenset({Material.FOREST, Material.DESERT, Material.SWAMP, Material.MOUNTAIN})
# Tiles placed by terrain detail generator within regions (epic-09)
DETAIL_TILES = frozenset({Material.FLOOR, Material.WALL, Material.WATER, Material.LAVA, Material.BRIDGE})


class TestVoronoiTessellation(unittest.TestCase):
    """Test that the Voronoi region generation creates a gapless map."""

    @classmethod
    def setUpClass(cls):
        cfg = SimulationConfig()
        cls.mgr = EngineManager(cfg)
        snap = cls.mgr.get_snapshot()
        cls.snap = snap
        cls.cfg = cfg

    def test_no_floor_tiles_outside_town(self):
        """FLOOR tiles outside town should be limited to terrain detail (clearings/valleys)."""
        grid = self.snap.grid
        floor_count = 0
        for y in range(self.cfg.grid_height):
            for x in range(self.cfg.grid_width):
                pos = Vector2(x, y)
                tile = grid.get(pos)
                if tile == Material.FLOOR:
                    floor_count += 1
        # Terrain detail adds clearings/valleys — allow up to 40%
        total_tiles = self.cfg.grid_width * self.cfg.grid_height
        floor_pct = floor_count / total_tiles * 100
        self.assertLess(floor_pct, 40.0,
                        f"{floor_count} FLOOR tiles ({floor_pct:.1f}%) — should be <40%")

    def test_regions_cover_map(self):
        """Region terrain + overlays + detail + town should account for nearly all tiles."""
        grid = self.snap.grid
        categorized = 0
        for y in range(self.cfg.grid_height):
            for x in range(self.cfg.grid_width):
                tile = grid.get(Vector2(x, y))
                if tile in TOWN_TILES or tile in TERRAIN_TILES or tile in OVERLAY_TILES or tile in DETAIL_TILES:
                    categorized += 1
        total = self.cfg.grid_width * self.cfg.grid_height
        coverage = categorized / total * 100
        self.assertGreater(coverage, 99.0,
                           f"Only {coverage:.1f}% of tiles are categorized — expected >99%")

    def test_regions_border_each_other(self):
        """At least some tiles should have a neighbor belonging to a different region."""
        regions = list(self.snap.regions)
        if len(regions) < 2:
            self.skipTest("Need at least 2 regions")

        border_count = 0
        grid = self.snap.grid
        for y in range(1, self.cfg.grid_height - 1):
            for x in range(1, self.cfg.grid_width - 1):
                pos = Vector2(x, y)
                tile = grid.get(pos)
                if tile not in TERRAIN_TILES:
                    continue
                # Check right neighbor
                right = Vector2(x + 1, y)
                right_tile = grid.get(right)
                if right_tile in TERRAIN_TILES and right_tile != tile:
                    border_count += 1
                    if border_count >= 10:
                        break
            if border_count >= 10:
                break
        self.assertGreater(border_count, 0,
                           "No region borders found — regions should share borders")

    def test_all_regions_have_territory(self):
        """Each region should own at least some tiles."""
        regions = list(self.snap.regions)
        grid = self.snap.grid
        for region in regions:
            # Check center tile is the region's terrain
            center_tile = grid.get(region.center)
            self.assertIn(center_tile,
                          {region.terrain} | OVERLAY_TILES | DETAIL_TILES,
                          f"Region '{region.name}' center at {region.center} has "
                          f"tile {center_tile}, expected {region.terrain} or detail")


class TestFindRegionAt(unittest.TestCase):
    """Test the find_region_at Voronoi lookup function."""

    def test_returns_nearest(self):
        r1 = Region(region_id="r1", name="R1", terrain=Material.FOREST,
                     center=Vector2(30, 30), radius=50, difficulty=1)
        r2 = Region(region_id="r2", name="R2", terrain=Material.DESERT,
                     center=Vector2(100, 100), radius=50, difficulty=2)
        # Point closer to r1
        result = find_region_at(Vector2(40, 40), [r1, r2])
        self.assertEqual(result.region_id, "r1")
        # Point closer to r2
        result = find_region_at(Vector2(90, 90), [r1, r2])
        self.assertEqual(result.region_id, "r2")

    def test_empty_regions_returns_none(self):
        result = find_region_at(Vector2(50, 50), [])
        self.assertIsNone(result)

    def test_equidistant_returns_first(self):
        r1 = Region(region_id="r1", name="R1", terrain=Material.FOREST,
                     center=Vector2(0, 0), radius=50, difficulty=1)
        r2 = Region(region_id="r2", name="R2", terrain=Material.DESERT,
                     center=Vector2(10, 0), radius=50, difficulty=2)
        # Exactly equidistant at (5, 0): manhattan to r1=5, to r2=5 → first wins
        result = find_region_at(Vector2(5, 0), [r1, r2])
        self.assertEqual(result.region_id, "r1")

    def test_single_region_always_matches(self):
        r = Region(region_id="r1", name="R1", terrain=Material.FOREST,
                   center=Vector2(50, 50), radius=10, difficulty=1)
        # Even far away, single region always matches
        result = find_region_at(Vector2(180, 180), [r])
        self.assertEqual(result.region_id, "r1")


if __name__ == "__main__":
    unittest.main()
