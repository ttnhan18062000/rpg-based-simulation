"""Terrain Detail Generator — adds intra-region variety (epic-09).

After Voronoi paints each region with a uniform terrain type, this generator
adds natural features: clearings, water bodies, cliff faces, paths, bridges,
lava vents, dense groves, etc.  Each biome has its own detail pass.

All generation is deterministic via DeterministicRNG.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.enums import Domain, Material
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.core.grid import Grid
    from src.core.regions import Region
    from src.systems.rng import DeterministicRNG


# ---------------------------------------------------------------------------
# Per-biome feature specs
# ---------------------------------------------------------------------------
# Each spec defines: (feature_material, chance_per_tile, cluster_size_range,
#                      min_count, max_count_per_region)
# "chance_per_tile" is checked per tile; "cluster" means we paint a blob.

_BIOME_FEATURES: dict[int, list[dict]] = {
    Material.FOREST: [
        # Clearings (open floor areas amid dense forest)
        {"name": "clearing", "mat": Material.FLOOR, "chance": 0.06,
         "cluster_min": 2, "cluster_max": 5},
        # Dense groves (impassable thick trees)
        {"name": "dense_grove", "mat": Material.WALL, "chance": 0.03,
         "cluster_min": 1, "cluster_max": 3},
        # Forest streams (narrow water lines)
        {"name": "stream", "type": "river", "width": 1, "count_min": 1, "count_max": 2},
        # Forest paths connecting locations
        {"name": "path", "type": "road_network"},
    ],
    Material.DESERT: [
        # Rocky ridges (impassable stone outcrops)
        {"name": "ridge", "mat": Material.WALL, "chance": 0.04,
         "cluster_min": 2, "cluster_max": 4},
        # Oases (rare water patches)
        {"name": "oasis", "mat": Material.WATER, "chance": 0.008,
         "cluster_min": 2, "cluster_max": 4},
        # Hard-packed ground (walkable floor patches)
        {"name": "hard_ground", "mat": Material.FLOOR, "chance": 0.05,
         "cluster_min": 1, "cluster_max": 3},
        # Caravan routes
        {"name": "caravan_route", "type": "road_network"},
    ],
    Material.SWAMP: [
        # Stagnant pools (impassable water)
        {"name": "pool", "mat": Material.WATER, "chance": 0.12,
         "cluster_min": 2, "cluster_max": 5},
        # Dead trees / thickets (impassable)
        {"name": "thicket", "mat": Material.WALL, "chance": 0.03,
         "cluster_min": 1, "cluster_max": 2},
        # Mudflats (walkable clearings)
        {"name": "mudflat", "mat": Material.FLOOR, "chance": 0.04,
         "cluster_min": 1, "cluster_max": 3},
        # Bog paths with bridges over water
        {"name": "bog_path", "type": "road_network"},
    ],
    Material.MOUNTAIN: [
        # Cliff faces (impassable rock walls)
        {"name": "cliff", "mat": Material.WALL, "chance": 0.08,
         "cluster_min": 2, "cluster_max": 5},
        # Valleys (open floor areas between peaks)
        {"name": "valley", "mat": Material.FLOOR, "chance": 0.06,
         "cluster_min": 2, "cluster_max": 4},
        # Lava vents (high difficulty only, rare)
        {"name": "lava_vent", "mat": Material.LAVA, "chance": 0.015,
         "cluster_min": 1, "cluster_max": 2, "min_difficulty": 3},
        # Mountain passes
        {"name": "pass", "type": "road_network"},
    ],
}


class TerrainDetailGenerator:
    """Adds intra-region terrain detail after Voronoi assignment.

    Thread-safe: only called during world build.
    Deterministic: all randomness via DeterministicRNG.
    """

    __slots__ = ("_grid", "_rng")

    def __init__(self, grid: Grid, rng: DeterministicRNG) -> None:
        self._grid = grid
        self._rng = rng

    def generate_all(self, regions: list[Region]) -> None:
        """Run detail passes for every region."""
        for idx, region in enumerate(regions):
            self._detail_region(region, idx)

    def _detail_region(self, region: Region, region_idx: int) -> None:
        """Apply biome-specific detail to a single region."""
        features = _BIOME_FEATURES.get(int(region.terrain))
        if not features:
            return

        grid = self._grid
        rng = self._rng
        base_mat = region.terrain
        cx, cy = region.center.x, region.center.y
        radius = region.radius

        for fi, feat in enumerate(features):
            # Skip difficulty-gated features
            min_diff = feat.get("min_difficulty", 0)
            if min_diff and region.difficulty < min_diff:
                continue

            feat_type = feat.get("type")

            if feat_type == "river":
                self._place_river(region, region_idx, fi, feat)
            elif feat_type == "road_network":
                self._place_road_network(region, region_idx, fi)
            else:
                # Scatter-based feature (clusters)
                self._place_scatter(region, region_idx, fi, feat)

    def _place_scatter(self, region: Region, ridx: int, fidx: int, feat: dict) -> None:
        """Place scattered clusters of a material within the region."""
        grid = self._grid
        rng = self._rng
        base_mat = region.terrain
        target_mat = Material(feat["mat"])
        chance = feat["chance"]
        cluster_min = feat.get("cluster_min", 1)
        cluster_max = feat.get("cluster_max", 3)
        cx, cy = region.center.x, region.center.y
        radius = region.radius

        # Scan tiles within region radius
        seed_base = ridx * 1000 + fidx * 100
        placed = 0
        max_features = max(3, int(radius * radius * chance * 0.3))

        for y in range(max(0, cy - radius), min(grid.height, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(grid.width, cx + radius + 1)):
                if placed >= max_features:
                    return
                pos = Vector2(x, y)
                if grid.get(pos) != base_mat:
                    continue
                # Deterministic chance check
                tile_seed = seed_base + y * grid.width + x
                roll = rng.next_float(Domain.MAP_GEN, tile_seed, ridx + fidx * 50)
                if roll >= chance:
                    continue
                # Place a cluster centered here
                csize = rng.next_int(Domain.MAP_GEN, tile_seed, ridx + 300,
                                     cluster_min, cluster_max)
                self._paint_cluster(x, y, csize, target_mat, base_mat)
                placed += 1

    def _paint_cluster(
        self, cx: int, cy: int, size: int, mat: Material, base_mat: Material
    ) -> None:
        """Paint a small blob of *mat* around (cx, cy), only overwriting *base_mat*."""
        grid = self._grid
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                if abs(dx) + abs(dy) > size:
                    continue
                pos = Vector2(cx + dx, cy + dy)
                if grid.in_bounds(pos) and grid.get(pos) == base_mat:
                    grid.set(pos, mat)

    def _place_river(self, region: Region, ridx: int, fidx: int, feat: dict) -> None:
        """Place a winding river/stream through the region."""
        grid = self._grid
        rng = self._rng
        base_mat = region.terrain
        cx, cy = region.center.x, region.center.y
        radius = region.radius
        width = feat.get("width", 1)
        count_min = feat.get("count_min", 1)
        count_max = feat.get("count_max", 1)

        num_rivers = rng.next_int(Domain.MAP_GEN, ridx * 200 + fidx, 0,
                                  count_min, count_max)

        for ri in range(num_rivers):
            seed = ridx * 500 + fidx * 50 + ri
            # Pick start edge: top or left of region
            if rng.next_bool(Domain.MAP_GEN, seed, 1, 0.5):
                # Horizontal river (left to right)
                start_y = cy + rng.next_int(Domain.MAP_GEN, seed, 2,
                                            -radius // 3, radius // 3)
                ry = start_y
                for rx in range(max(0, cx - radius), min(grid.width, cx + radius + 1)):
                    pos = Vector2(rx, ry)
                    if grid.in_bounds(pos) and grid.get(pos) == base_mat:
                        grid.set(pos, Material.WATER)
                        # Paint width
                        for w in range(1, width + 1):
                            wp = Vector2(rx, ry + w)
                            if grid.in_bounds(wp) and grid.get(wp) == base_mat:
                                grid.set(wp, Material.WATER)
                    # Wander the river path
                    drift = rng.next_int(Domain.MAP_GEN, seed + rx, 10, -1, 1)
                    ry = max(0, min(grid.height - 1, ry + drift))
            else:
                # Vertical river (top to bottom)
                start_x = cx + rng.next_int(Domain.MAP_GEN, seed, 3,
                                            -radius // 3, radius // 3)
                rx = start_x
                for ry in range(max(0, cy - radius), min(grid.height, cy + radius + 1)):
                    pos = Vector2(rx, ry)
                    if grid.in_bounds(pos) and grid.get(pos) == base_mat:
                        grid.set(pos, Material.WATER)
                        for w in range(1, width + 1):
                            wp = Vector2(rx + w, ry)
                            if grid.in_bounds(wp) and grid.get(wp) == base_mat:
                                grid.set(wp, Material.WATER)
                    drift = rng.next_int(Domain.MAP_GEN, seed + ry, 11, -1, 1)
                    rx = max(0, min(grid.width - 1, rx + drift))

            # Place bridges where river crosses the region center ± a few tiles
            self._place_bridges_near(region, ri)

    def _place_bridges_near(self, region: Region, river_idx: int) -> None:
        """Place BRIDGE tiles at 2-3 points where WATER meets the region center area."""
        grid = self._grid
        rng = self._rng
        cx, cy = region.center.x, region.center.y
        bridge_range = max(region.radius // 3, 4)

        bridges_placed = 0
        for y in range(max(0, cy - bridge_range), min(grid.height, cy + bridge_range + 1)):
            for x in range(max(0, cx - bridge_range), min(grid.width, cx + bridge_range + 1)):
                if bridges_placed >= 3:
                    return
                pos = Vector2(x, y)
                if grid.get(pos) != Material.WATER:
                    continue
                # Place bridge if this water tile has walkable neighbors on opposite sides
                has_n = grid.in_bounds_xy(x, y - 1) and grid.get_xy(x, y - 1) not in (
                    Material.WATER, Material.WALL, Material.LAVA)
                has_s = grid.in_bounds_xy(x, y + 1) and grid.get_xy(x, y + 1) not in (
                    Material.WATER, Material.WALL, Material.LAVA)
                has_w = grid.in_bounds_xy(x - 1, y) and grid.get_xy(x - 1, y) not in (
                    Material.WATER, Material.WALL, Material.LAVA)
                has_e = grid.in_bounds_xy(x + 1, y) and grid.get_xy(x + 1, y) not in (
                    Material.WATER, Material.WALL, Material.LAVA)
                if (has_n and has_s) or (has_w and has_e):
                    grid.set(pos, Material.BRIDGE)
                    bridges_placed += 1

    def _place_road_network(self, region: Region, ridx: int, fidx: int) -> None:
        """Connect locations within a region with ROAD/BRIDGE paths."""
        grid = self._grid
        base_mat = region.terrain
        locs = region.locations
        if len(locs) < 2:
            return

        # Connect each location to its nearest neighbor (simple MST-like)
        connected: set[int] = {0}
        edges: list[tuple[int, int]] = []

        while len(connected) < len(locs):
            best_dist = float("inf")
            best_from = -1
            best_to = -1
            for ci in connected:
                for ti in range(len(locs)):
                    if ti in connected:
                        continue
                    d = locs[ci].pos.manhattan(locs[ti].pos)
                    if d < best_dist:
                        best_dist = d
                        best_from = ci
                        best_to = ti
            if best_to < 0:
                break
            connected.add(best_to)
            edges.append((best_from, best_to))

        # Draw L-shaped roads between connected locations
        for fi, ti in edges:
            fp = locs[fi].pos
            tp = locs[ti].pos
            self._draw_road_path(fp, tp, base_mat)

    def _draw_road_path(self, start: Vector2, end: Vector2, base_mat: Material) -> None:
        """Draw an L-shaped road/bridge path from start to end."""
        grid = self._grid
        x, y = start.x, start.y
        tx, ty = end.x, end.y

        # Horizontal first, then vertical
        step_x = 1 if tx > x else -1
        while x != tx:
            x += step_x
            pos = Vector2(x, y)
            if grid.in_bounds(pos):
                mat = grid.get(pos)
                if mat == Material.WATER:
                    grid.set(pos, Material.BRIDGE)
                elif mat == base_mat:
                    grid.set(pos, Material.ROAD)

        step_y = 1 if ty > y else -1
        while y != ty:
            y += step_y
            pos = Vector2(x, y)
            if grid.in_bounds(pos):
                mat = grid.get(pos)
                if mat == Material.WATER:
                    grid.set(pos, Material.BRIDGE)
                elif mat == base_mat:
                    grid.set(pos, Material.ROAD)
