"""Tests for src.rendering.shape's connected-component fill-ratio and rotation detection.

TCK-20260821-VISUAL-SHAPE-METRIC. Synthetic-fixture tests use plain
terrain: dict[tuple[int, int], str] fixtures directly (connected_components,
compute_bbox, compute_fill_ratio, and detect_rotation_match are pure geometry over raw
dict/ShapeComponent input, no AuthoritativeState construction needed). Real-corpus tests
load dungeon_crawl via WorldRepository -> WorldCompiler.compile(spec, seed=42) (tick 0, no
Kernel.tick_once() calls), the same invocation shape test_connectivity.py and
test_density.py already established.

Test 11 (the literal historical 26/33 corpus reproduction via a hardcoded 3-world
exclusion list) is deliberately NOT implemented here -- see
staging_artifacts/TCK-20260821-VISUAL-SHAPE-METRIC/plan.md's "Decision: AC #4 Corpus
Scope" section. Test 10 below asserts the qualitative, corpus-size-independent invariant
instead (every sub-0.95 component is FOREST type), which holds identically regardless of
how many worlds data/worlds/ currently contains.
"""
from __future__ import annotations

import ast
from pathlib import Path

from src.rendering.shape import (
    ShapeComponent,
    compute_bbox,
    compute_fill_ratio,
    connected_components,
    detect_rotation_match,
    group_terrain_by_type,
)
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

_SHAPE_MODULE_PATH = Path(__file__).resolve().parents[3] / "src" / "rendering" / "shape.py"


def _component(
    terrain_type: str, tiles: set[tuple[int, int]]
) -> ShapeComponent:
    frozen_tiles = frozenset(tiles)
    return ShapeComponent(
        terrain_type=terrain_type,
        tiles=frozen_tiles,
        size=len(frozen_tiles),
        bbox=compute_bbox(frozen_tiles),
        fill_ratio=compute_fill_ratio(frozen_tiles),
    )


def test_connected_component_labeling_splits_disjoint_same_type_patches():
    terrain: dict[tuple[int, int], str] = {}
    # Patch A: 5x5 FOREST block (25 tiles) at x in [0, 4]
    for x in range(5):
        for y in range(5):
            terrain[(x, y)] = "forest"
    # Gap column of a different terrain type separates the two patches
    for y in range(5):
        terrain[(5, y)] = "cave"
    # Patch B: 5x5 FOREST block (25 tiles) at x in [6, 10], disjoint from patch A
    for x in range(6, 11):
        for y in range(5):
            terrain[(x, y)] = "forest"

    components = connected_components(terrain, min_size=1)
    forest_components = [c for c in components if c.terrain_type == "forest"]

    assert len(forest_components) == 2
    assert {c.size for c in forest_components} == {25, 25}


def test_dungeon_crawl_forest_is_two_components_of_1116_tiles_each():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state, _report = WorldCompiler.compile(spec, seed=42)

    components = connected_components(state.terrain)
    forest_components = [c for c in components if c.terrain_type == "forest"]

    assert len(forest_components) == 2
    assert [c.size for c in forest_components] == [1116, 1116]


def test_dungeon_crawl_per_component_fill_ratios_match_documented_evidence():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state, _report = WorldCompiler.compile(spec, seed=42)

    components = connected_components(state.terrain)
    by_type: dict[str, list[ShapeComponent]] = {}
    for c in components:
        by_type.setdefault(c.terrain_type, []).append(c)

    cave = by_type["cave"]
    forest = by_type["forest"]
    ruin = by_type["ruin"]

    assert len(cave) == 1
    assert round(cave[0].fill_ratio, 3) == 0.980
    assert len(forest) == 2
    assert round(forest[0].fill_ratio, 3) == 1.000
    assert round(forest[1].fill_ratio, 3) == 1.000
    assert len(ruin) == 1
    assert round(ruin[0].fill_ratio, 3) == 1.000


def test_fill_ratio_formula_on_synthetic_shapes():
    # Perfect 4x4 square: 16 tiles, bbox area 16 -> fill_ratio == 1.0
    square = {(x, y) for x in range(4) for y in range(4)}
    assert compute_fill_ratio(square) == 1.0

    # L-shape inscribed in a 3x3 bounding box (9 cells) missing the top-right corner:
    # 8 tiles / 9 bbox area
    l_shape = {(x, y) for x in range(3) for y in range(3)} - {(2, 2)}
    assert compute_fill_ratio(l_shape) == 8 / 9

    # Single tile: 1x1 bounding box, fill_ratio == 1.0
    single = {(5, 5)}
    assert compute_fill_ratio(single) == 1.0


def test_forest_components_detected_as_90_degree_rotation():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state, _report = WorldCompiler.compile(spec, seed=42)

    components = connected_components(state.terrain)
    forest_components = [c for c in components if c.terrain_type == "forest"]
    assert len(forest_components) == 2

    a, b = forest_components
    assert detect_rotation_match(a, b) is True


def test_rotation_detection_rejects_non_rotated_shapes():
    # L-shape (3x2 bbox), missing bottom-right cell.
    a_tiles = {(x, y) for x in range(3) for y in range(2)} - {(2, 1)}
    a = _component("forest", a_tiles)

    # A different shape with swapped bbox dims (2x3) that is NOT a rotation of `a`:
    # a full 2x3 rectangle (6 tiles) vs. a's 5 tiles -- different tile-set content
    # entirely, not just a differently-shaped hole.
    b_tiles = {(x, y) for x in range(2) for y in range(3)}
    b = _component("forest", b_tiles)

    assert detect_rotation_match(a, b) is False


def test_rotation_detection_on_solid_rectangles_is_not_over_claimed():
    # Two solid same-area rectangles with swapped dimensions: 4-wide x 3-tall and
    # 3-wide x 4-tall. All three transforms (transpose, rotate-CW, rotate-CCW)
    # independently match for a solid rectangle -- documents the caveat that this
    # doesn't by itself prove "true rotation" for such shapes.
    a_tiles = {(x, y) for x in range(4) for y in range(3)}
    b_tiles = {(x, y) for x in range(3) for y in range(4)}
    a = _component("cave", a_tiles)
    b = _component("cave", b_tiles)

    a_norm_min_x, a_norm_min_y, _, _ = a.bbox
    b_norm_min_x, b_norm_min_y, _, _ = b.bbox
    from src.rendering.shape import _normalize

    a_norm = _normalize(a.tiles, a_norm_min_x, a_norm_min_y)
    b_norm = _normalize(b.tiles, b_norm_min_x, b_norm_min_y)

    w_a = a.bbox[2] - a.bbox[0]
    h_a = a.bbox[3] - a.bbox[1]

    transpose = frozenset((y, x) for x, y in a_norm)
    rotate_cw = frozenset((y, w_a - x) for x, y in a_norm)
    rotate_ccw = frozenset((h_a - y, x) for x, y in a_norm)

    assert b_norm == transpose
    assert b_norm == rotate_cw
    assert b_norm == rotate_ccw
    assert detect_rotation_match(a, b) is True


def test_min_component_size_filter_excludes_small_fragments():
    terrain: dict[tuple[int, int], str] = {}
    # Real patch: 5x5 cave block (25 tiles), well above the min_size=20 default.
    for x in range(5):
        for y in range(5):
            terrain[(x, y)] = "cave"
    # Tiny noise fragment of the same terrain type, disconnected from the real patch
    # (3 tiles, far away so BFS never connects them).
    terrain[(100, 100)] = "cave"
    terrain[(101, 100)] = "cave"
    terrain[(100, 101)] = "cave"

    components = connected_components(terrain, min_size=20)

    assert len(components) == 1
    assert components[0].size == 25


def test_plain_and_road_excluded_case_insensitively():
    terrain: dict[tuple[int, int], str] = {}
    for x in range(6):
        for y in range(6):
            terrain[(x, y)] = "cave"
    for x in range(20, 26):
        for y in range(6):
            terrain[(x, y)] = "PLAIN"
    for x in range(40, 46):
        for y in range(6):
            terrain[(x, y)] = "plain"
    for x in range(60, 66):
        for y in range(6):
            terrain[(x, y)] = "ROAD"
    for x in range(80, 86):
        for y in range(6):
            terrain[(x, y)] = "road"

    components = connected_components(terrain, min_size=1)

    assert len(components) == 1
    assert components[0].terrain_type == "cave"


def test_corpus_wide_sweep_every_below_threshold_component_is_forest():
    repo = WorldRepository("data/worlds")
    world_ids = repo.list_worlds()
    assert len(world_ids) > 0

    below_threshold: list[ShapeComponent] = []
    for world_id in world_ids:
        spec = repo.load_world(world_id)
        state, _report = WorldCompiler.compile(spec, seed=42)
        components = connected_components(state.terrain)
        below_threshold.extend(c for c in components if c.fill_ratio < 0.95)

    assert len(below_threshold) > 0
    assert all(c.terrain_type.upper() == "FOREST" for c in below_threshold)


def test_shape_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline():
    tree = ast.parse(_SHAPE_MODULE_PATH.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names = [
                base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                for base in node.bases
            ]
            assert "PillarScorer" not in base_names, "shape.py must not subclass PillarScorer"
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "simulation_quality" not in name, f"shape.py must not import {name}"
            assert "observability.events" not in name, f"shape.py must not import {name}"


def test_shape_module_has_zero_image_or_render_dependency():
    tree = ast.parse(_SHAPE_MODULE_PATH.read_text())
    forbidden_substrings = ("png_writer", "rendering.render", "rendering.incremental", "PIL", "Pillow")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert not any(forbidden in name for forbidden in forbidden_substrings), (
                f"shape.py must not import {name} (image/render dependency)"
            )


def test_does_not_mutate_authoritative_state():
    terrain: dict[tuple[int, int], str] = {}
    for x in range(6):
        for y in range(6):
            terrain[(x, y)] = "forest"
    terrain[(10, 10)] = "PLAIN"

    terrain_before = dict(terrain)

    grouped_1 = group_terrain_by_type(terrain)
    grouped_2 = group_terrain_by_type(terrain)
    result_1 = connected_components(terrain, min_size=1)
    result_2 = connected_components(terrain, min_size=1)

    assert grouped_1 == grouped_2
    assert result_1 == result_2
    assert terrain == terrain_before
