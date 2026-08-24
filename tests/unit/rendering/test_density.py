"""Tests for src.rendering.density's nearest-neighbor CV and terrain histogram.

TCK-20260821-VISUAL-DENSITY-METRIC. Synthetic-fixture tests use minimal EntityState
instances (or plain terrain dicts) directly -- both compute_density_cv and
compute_terrain_histogram are pure geometry/counting over raw dict input, no
AuthoritativeState construction needed. The real-corpus tests load sandbox_world and
dungeon_crawl to reproduce the documented evidence (~0.648 / ~0.678), same
WorldRepository -> WorldCompiler.compile(spec, seed=42) invocation pattern
test_connectivity.py's own real-corpus test uses.
"""
from __future__ import annotations

import ast
import statistics
from pathlib import Path

from src.core.state import EntityState, LifecycleComponent, NavigationComponent
from src.rendering.density import compute_density_cv, compute_terrain_histogram
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

_DENSITY_MODULE_PATH = Path(__file__).resolve().parents[3] / "src" / "rendering" / "density.py"


def _entity(entity_id: int, position: tuple[float, float], active: bool = True) -> EntityState:
    return EntityState(
        id=entity_id,
        kind="hero",
        navigation=NavigationComponent(position=position),
        lifecycle=LifecycleComponent(active=active),
    )


def test_sandbox_world_reproduces_documented_cv():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("sandbox_world")
    state, _report = WorldCompiler.compile(spec, seed=42)

    result = compute_density_cv(state.entities)

    assert round(result.cv, 3) == 0.648


def test_dungeon_crawl_reproduces_documented_cv():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state, _report = WorldCompiler.compile(spec, seed=42)

    result = compute_density_cv(state.entities)

    assert round(result.cv, 3) == 0.678


def test_population_stdev_not_sample_stdev():
    # Hand-computed: entities at (0,0), (1,0), (3,0). nn_distances = [1, 1, 2].
    # mean = 4/3. population stdev = sqrt(2/9) = sqrt(2)/3 -> cv = sqrt(2)/4 = 0.3535533905932738
    # sample stdev (ddof=1) would instead give cv = 0.4330127018922193 -- a visibly
    # different, wrong number if statistics.stdev() were used by mistake.
    entities = {
        1: _entity(1, (0.0, 0.0)),
        2: _entity(2, (1.0, 0.0)),
        3: _entity(3, (3.0, 0.0)),
    }

    result = compute_density_cv(entities)

    expected_population_cv = statistics.pstdev([1.0, 1.0, 2.0]) / statistics.mean([1.0, 1.0, 2.0])
    wrong_sample_cv = statistics.stdev([1.0, 1.0, 2.0]) / statistics.mean([1.0, 1.0, 2.0])

    assert abs(result.cv - expected_population_cv) < 1e-9
    assert abs(result.cv - 0.3535533905932738) < 1e-9
    assert abs(result.cv - wrong_sample_cv) > 1e-3


def test_two_entities_minimum_nn_distance():
    entities = {
        1: _entity(1, (0.0, 0.0)),
        2: _entity(2, (3.0, 4.0)),
    }

    result = compute_density_cv(entities)

    assert result.entity_count == 2
    assert result.nn_distances == [5.0, 5.0]
    assert result.cv == 0.0


def test_inactive_entities_excluded_from_cv():
    baseline_entities = {
        1: _entity(1, (0.0, 0.0)),
        2: _entity(2, (1.0, 0.0)),
        3: _entity(3, (3.0, 0.0)),
    }
    with_inactive = dict(baseline_entities)
    with_inactive[4] = _entity(4, (1000.0, 1000.0), active=False)

    baseline_result = compute_density_cv(baseline_entities)
    with_inactive_result = compute_density_cv(with_inactive)

    assert with_inactive_result == baseline_result


def test_terrain_histogram_sums_to_terrain_tile_count():
    terrain = {
        (0, 0): "PLAIN",
        (1, 0): "PLAIN",
        (2, 0): "plain",
        (0, 1): "WALL",
        (1, 1): "FOREST",
    }

    histogram = compute_terrain_histogram(terrain)

    assert sum(histogram.values()) == len(terrain)
    assert histogram["PLAIN"] == 2
    assert histogram["plain"] == 1
    assert "PLAIN" in histogram and "plain" in histogram


def test_dungeon_crawl_histogram_matches_terrain_tile_count():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state, _report = WorldCompiler.compile(spec, seed=42)

    histogram = compute_terrain_histogram(state.terrain)

    assert sum(histogram.values()) == len(state.terrain)


def test_density_module_has_zero_image_or_render_dependency():
    tree = ast.parse(_DENSITY_MODULE_PATH.read_text())
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
                f"density.py must not import {name} (image/render dependency)"
            )


def test_density_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline():
    tree = ast.parse(_DENSITY_MODULE_PATH.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names = [
                base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                for base in node.bases
            ]
            assert "PillarScorer" not in base_names, "density.py must not subclass PillarScorer"
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "simulation_quality" not in name, f"density.py must not import {name}"
            assert "observability.events" not in name, f"density.py must not import {name}"


def test_does_not_mutate_authoritative_state():
    entities = {
        1: _entity(1, (0.0, 0.0)),
        2: _entity(2, (1.0, 0.0)),
        3: _entity(3, (3.0, 0.0)),
    }
    terrain = {(0, 0): "PLAIN", (1, 0): "WALL", (2, 0): "plain"}

    entities_before = dict(entities)
    terrain_before = dict(terrain)

    density_result_1 = compute_density_cv(entities)
    density_result_2 = compute_density_cv(entities)
    histogram_result_1 = compute_terrain_histogram(terrain)
    histogram_result_2 = compute_terrain_histogram(terrain)

    assert density_result_1 == density_result_2
    assert histogram_result_1 == histogram_result_2
    assert entities == entities_before
    assert terrain == terrain_before
