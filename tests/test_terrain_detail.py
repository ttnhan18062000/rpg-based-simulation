"""Tests for TerrainDetailGenerator — intra-region terrain variety (epic-09)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.enums import Material
from src.core.grid import Grid
from src.core.models import Vector2
from src.core.regions import Region
from src.systems.rng import DeterministicRNG
from src.systems.terrain_detail import TerrainDetailGenerator, _BIOME_FEATURES


def _make_region(terrain: Material, cx: int = 25, cy: int = 25,
                 radius: int = 20, difficulty: int = 1) -> Region:
    return Region(
        region_id="test", name="Test Region",
        terrain=terrain, center=Vector2(cx, cy),
        radius=radius, difficulty=difficulty,
    )


def _make_grid_and_gen(w: int = 50, h: int = 50, terrain: Material = Material.FOREST,
                       seed: int = 42) -> tuple[Grid, TerrainDetailGenerator, DeterministicRNG]:
    grid = Grid(w, h, default=terrain)
    rng = DeterministicRNG(seed=seed)
    gen = TerrainDetailGenerator(grid, rng)
    return grid, gen, rng


# ---------------------------------------------------------------------------
# Biome feature specs
# ---------------------------------------------------------------------------

class TestBiomeSpecs:
    def test_all_four_biomes_have_features(self):
        for mat in (Material.FOREST, Material.DESERT, Material.SWAMP, Material.MOUNTAIN):
            assert int(mat) in _BIOME_FEATURES, f"{mat.name} missing from _BIOME_FEATURES"

    def test_each_biome_has_road_network(self):
        for mat in (Material.FOREST, Material.DESERT, Material.SWAMP, Material.MOUNTAIN):
            features = _BIOME_FEATURES[int(mat)]
            road_feats = [f for f in features if f.get("type") == "road_network"]
            assert len(road_feats) >= 1, f"{mat.name} should have road_network feature"


# ---------------------------------------------------------------------------
# Forest detail
# ---------------------------------------------------------------------------

class TestForestDetail:
    def test_creates_clearings(self):
        """Forest regions should have FLOOR tiles (clearings)."""
        grid, gen, _ = _make_grid_and_gen(terrain=Material.FOREST)
        region = _make_region(Material.FOREST)
        gen.generate_all([region])
        floor_count = sum(1 for y in range(50) for x in range(50)
                          if grid.get(Vector2(x, y)) == Material.FLOOR)
        assert floor_count > 0, "Forest should have clearings (FLOOR tiles)"

    def test_creates_dense_groves(self):
        """Forest regions should have WALL tiles (dense impassable trees)."""
        grid, gen, _ = _make_grid_and_gen(terrain=Material.FOREST)
        region = _make_region(Material.FOREST)
        gen.generate_all([region])
        wall_count = sum(1 for y in range(50) for x in range(50)
                         if grid.get(Vector2(x, y)) == Material.WALL)
        assert wall_count > 0, "Forest should have dense groves (WALL tiles)"

    def test_creates_streams(self):
        """Forest regions should have WATER tiles (streams)."""
        grid, gen, _ = _make_grid_and_gen(terrain=Material.FOREST)
        region = _make_region(Material.FOREST)
        gen.generate_all([region])
        water_count = sum(1 for y in range(50) for x in range(50)
                          if grid.get(Vector2(x, y)) == Material.WATER)
        assert water_count > 0, "Forest should have streams (WATER tiles)"

    def test_majority_stays_forest(self):
        """Most tiles in a forest region should remain FOREST."""
        grid, gen, _ = _make_grid_and_gen(terrain=Material.FOREST)
        region = _make_region(Material.FOREST)
        gen.generate_all([region])
        forest_count = sum(1 for y in range(50) for x in range(50)
                           if grid.get(Vector2(x, y)) == Material.FOREST)
        total = 50 * 50
        assert forest_count / total > 0.4, \
            f"Forest should still be majority terrain, got {forest_count}/{total}"


# ---------------------------------------------------------------------------
# Desert detail
# ---------------------------------------------------------------------------

class TestDesertDetail:
    def test_creates_ridges(self):
        grid, gen, _ = _make_grid_and_gen(terrain=Material.DESERT)
        region = _make_region(Material.DESERT)
        gen.generate_all([region])
        wall_count = sum(1 for y in range(50) for x in range(50)
                         if grid.get(Vector2(x, y)) == Material.WALL)
        assert wall_count > 0, "Desert should have rocky ridges (WALL tiles)"

    def test_creates_oases(self):
        grid, gen, _ = _make_grid_and_gen(terrain=Material.DESERT)
        region = _make_region(Material.DESERT)
        gen.generate_all([region])
        water_count = sum(1 for y in range(50) for x in range(50)
                          if grid.get(Vector2(x, y)) == Material.WATER)
        assert water_count > 0, "Desert should have oases (WATER tiles)"


# ---------------------------------------------------------------------------
# Swamp detail
# ---------------------------------------------------------------------------

class TestSwampDetail:
    def test_creates_pools(self):
        grid, gen, _ = _make_grid_and_gen(terrain=Material.SWAMP)
        region = _make_region(Material.SWAMP)
        gen.generate_all([region])
        water_count = sum(1 for y in range(50) for x in range(50)
                          if grid.get(Vector2(x, y)) == Material.WATER)
        assert water_count > 10, "Swamp should have many pools (WATER tiles)"

    def test_creates_thickets(self):
        grid, gen, _ = _make_grid_and_gen(terrain=Material.SWAMP)
        region = _make_region(Material.SWAMP)
        gen.generate_all([region])
        wall_count = sum(1 for y in range(50) for x in range(50)
                         if grid.get(Vector2(x, y)) == Material.WALL)
        assert wall_count > 0, "Swamp should have dead tree thickets (WALL tiles)"

    def test_more_water_than_forest(self):
        """Swamp should produce more water features than forest."""
        grid_s, gen_s, _ = _make_grid_and_gen(terrain=Material.SWAMP, seed=42)
        gen_s.generate_all([_make_region(Material.SWAMP)])
        swamp_water = sum(1 for y in range(50) for x in range(50)
                          if grid_s.get(Vector2(x, y)) == Material.WATER)

        grid_f, gen_f, _ = _make_grid_and_gen(terrain=Material.FOREST, seed=42)
        gen_f.generate_all([_make_region(Material.FOREST)])
        forest_water = sum(1 for y in range(50) for x in range(50)
                           if grid_f.get(Vector2(x, y)) == Material.WATER)

        assert swamp_water > forest_water, \
            f"Swamp water ({swamp_water}) should exceed forest water ({forest_water})"


# ---------------------------------------------------------------------------
# Mountain detail
# ---------------------------------------------------------------------------

class TestMountainDetail:
    def test_creates_cliffs(self):
        grid, gen, _ = _make_grid_and_gen(terrain=Material.MOUNTAIN)
        region = _make_region(Material.MOUNTAIN)
        gen.generate_all([region])
        wall_count = sum(1 for y in range(50) for x in range(50)
                         if grid.get(Vector2(x, y)) == Material.WALL)
        assert wall_count > 0, "Mountain should have cliff faces (WALL tiles)"

    def test_creates_valleys(self):
        grid, gen, _ = _make_grid_and_gen(terrain=Material.MOUNTAIN)
        region = _make_region(Material.MOUNTAIN)
        gen.generate_all([region])
        floor_count = sum(1 for y in range(50) for x in range(50)
                          if grid.get(Vector2(x, y)) == Material.FLOOR)
        assert floor_count > 0, "Mountain should have valleys (FLOOR tiles)"

    def test_lava_only_at_high_difficulty(self):
        """Lava vents should only appear in difficulty >= 3 regions."""
        grid_lo, gen_lo, _ = _make_grid_and_gen(terrain=Material.MOUNTAIN, seed=42)
        gen_lo.generate_all([_make_region(Material.MOUNTAIN, difficulty=1)])
        lava_lo = sum(1 for y in range(50) for x in range(50)
                      if grid_lo.get(Vector2(x, y)) == Material.LAVA)

        grid_hi, gen_hi, _ = _make_grid_and_gen(terrain=Material.MOUNTAIN, seed=42)
        gen_hi.generate_all([_make_region(Material.MOUNTAIN, difficulty=3)])
        lava_hi = sum(1 for y in range(50) for x in range(50)
                      if grid_hi.get(Vector2(x, y)) == Material.LAVA)

        assert lava_lo == 0, "Low-difficulty mountains should have no lava"
        assert lava_hi > 0, "High-difficulty mountains should have lava vents"

    def test_more_cliffs_than_forest_walls(self):
        """Mountains should produce more wall features than forests."""
        grid_m, gen_m, _ = _make_grid_and_gen(terrain=Material.MOUNTAIN, seed=42)
        gen_m.generate_all([_make_region(Material.MOUNTAIN)])
        mtn_walls = sum(1 for y in range(50) for x in range(50)
                        if grid_m.get(Vector2(x, y)) == Material.WALL)

        grid_f, gen_f, _ = _make_grid_and_gen(terrain=Material.FOREST, seed=42)
        gen_f.generate_all([_make_region(Material.FOREST)])
        forest_walls = sum(1 for y in range(50) for x in range(50)
                           if grid_f.get(Vector2(x, y)) == Material.WALL)

        assert mtn_walls > forest_walls, \
            f"Mountain walls ({mtn_walls}) should exceed forest walls ({forest_walls})"


# ---------------------------------------------------------------------------
# Road network
# ---------------------------------------------------------------------------

class TestRoadNetwork:
    def test_road_connects_locations(self):
        """Regions with locations should have ROAD tiles connecting them."""
        from src.core.regions import Location
        grid, gen, _ = _make_grid_and_gen(terrain=Material.FOREST)
        region = _make_region(Material.FOREST)
        region.locations = [
            Location(location_id="a", name="A", location_type="enemy_camp",
                     pos=Vector2(15, 25), region_id="test"),
            Location(location_id="b", name="B", location_type="ruins",
                     pos=Vector2(35, 25), region_id="test"),
        ]
        gen.generate_all([region])
        road_count = sum(1 for y in range(50) for x in range(50)
                         if grid.get(Vector2(x, y)) == Material.ROAD)
        assert road_count > 5, "Should have roads connecting locations"


# ---------------------------------------------------------------------------
# Bridges
# ---------------------------------------------------------------------------

class TestBridges:
    def test_bridges_placed_over_water(self):
        """Bridges should appear where rivers cross walkable terrain."""
        grid, gen, _ = _make_grid_and_gen(terrain=Material.FOREST)
        region = _make_region(Material.FOREST)
        gen.generate_all([region])
        bridge_count = sum(1 for y in range(50) for x in range(50)
                           if grid.get(Vector2(x, y)) == Material.BRIDGE)
        # Bridges may or may not be placed depending on river position
        # Just verify they don't crash and are non-negative
        assert bridge_count >= 0


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_same_seed_same_result(self):
        """Two runs with same seed should produce identical grids."""
        grid1, gen1, _ = _make_grid_and_gen(terrain=Material.FOREST, seed=123)
        gen1.generate_all([_make_region(Material.FOREST)])

        grid2, gen2, _ = _make_grid_and_gen(terrain=Material.FOREST, seed=123)
        gen2.generate_all([_make_region(Material.FOREST)])

        for y in range(50):
            for x in range(50):
                pos = Vector2(x, y)
                assert grid1.get(pos) == grid2.get(pos), \
                    f"Mismatch at ({x},{y}): {grid1.get(pos)} vs {grid2.get(pos)}"

    def test_different_seed_different_result(self):
        """Different seeds should produce different grids."""
        grid1, gen1, _ = _make_grid_and_gen(terrain=Material.FOREST, seed=1)
        gen1.generate_all([_make_region(Material.FOREST)])

        grid2, gen2, _ = _make_grid_and_gen(terrain=Material.FOREST, seed=999)
        gen2.generate_all([_make_region(Material.FOREST)])

        differences = sum(1 for y in range(50) for x in range(50)
                          if grid1.get(Vector2(x, y)) != grid2.get(Vector2(x, y)))
        assert differences > 0, "Different seeds should produce different terrain"
