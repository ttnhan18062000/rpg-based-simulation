"""Tests for src.rendering.variants's trail-activity liveliness and cross-spec TVD.

TCK-20260821-VISUAL-VARIANTS-METRIC. Synthetic-fixture tests use minimal EntityState
instances (or plain dict fixtures) directly -- normalize_histogram,
total_variation_distance, compute_trail_activity, and select_trail_entity are all pure
functions over raw dict/primitive input, no AuthoritativeState construction needed. The
real-corpus tests load sandbox_world and dungeon_crawl to reproduce the documented TVD
anchor, same WorldRepository -> WorldCompiler.compile(spec, seed=N) invocation pattern
test_density.py's and test_shape.py's own real-corpus tests use.

Test 11 (test_render_trail_prototype_and_variants_module_selection_agree) is
deliberately NOT implemented here -- per plan.md's Decision 5, render_trail.py stays a
frozen, read-only prototype that this ticket does not rewire to delegate to
select_trail_entity.
"""
from __future__ import annotations

import ast
from pathlib import Path

from src.core.state import EntityState, LifecycleComponent, NavigationComponent
from src.rendering.density import compute_terrain_histogram
from src.rendering.variants import (
    compute_trail_activity,
    normalize_histogram,
    select_trail_entity,
    total_variation_distance,
)
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

_VARIANTS_MODULE_PATH = Path(__file__).resolve().parents[3] / "src" / "rendering" / "variants.py"


def _entity(entity_id: int, position: tuple[float, float], active: bool = True) -> EntityState:
    return EntityState(
        id=entity_id,
        kind="hero",
        navigation=NavigationComponent(position=position),
        lifecycle=LifecycleComponent(active=active),
    )


def test_total_variation_distance_reproduces_sandbox_dungeon_anchor():
    # Verified value is 0.23161981243456373 (round(x, 4) == 0.2316), independently
    # reproduced this session -- not the PROPOSAL.md-rounded 0.2315, to avoid a test
    # that passes by coincidence of rounding direction.
    repo = WorldRepository("data/worlds")
    sandbox_spec = repo.load_world("sandbox_world")
    sandbox_state, _report = WorldCompiler.compile(sandbox_spec, seed=42)
    dungeon_spec = repo.load_world("dungeon_crawl")
    dungeon_state, _report = WorldCompiler.compile(dungeon_spec, seed=42)

    h1 = normalize_histogram(compute_terrain_histogram(sandbox_state.terrain))
    h2 = normalize_histogram(compute_terrain_histogram(dungeon_state.terrain))

    result = total_variation_distance(h1, h2)

    assert round(result, 4) == 0.2316


def test_total_variation_distance_formula_on_synthetic_histograms():
    assert total_variation_distance({"A": 1.0}, {"B": 1.0}) == 1.0

    same = {"A": 0.5, "B": 0.5}
    assert total_variation_distance(same, same) == 0.0

    # Hand-computed partial overlap: 0.5 * (|0.6-0.4| + |0.4-0.6|) = 0.5 * 0.4 = 0.2
    h1 = {"A": 0.6, "B": 0.4}
    h2 = {"A": 0.4, "B": 0.6}
    assert round(total_variation_distance(h1, h2), 9) == 0.2


def test_total_variation_distance_same_spec_different_seed_is_zero_for_dungeon_crawl():
    # dungeon_crawl, not sandbox_world, is the same-spec/different-seed anchor here --
    # dungeon_crawl's four composed modules (ruins_mystery_quest, goblin_camp_conflict,
    # old_mine_resource_loop, scalable_bandit_camp) declare zero terrain_variants fields,
    # so its seed-invariance is structural. sandbox_world's current seed-invariance is
    # instead an artifact of WorldRepository.load_world() redirecting to a stale
    # resolved/world.resolved.yaml cache that predates wolf_den_near_forest.yaml's
    # terrain_variants field (plan.md Decision 1, investigation.md's stale-cache
    # finding) -- do not "fix" this anchor back to sandbox_world without re-reading that
    # reasoning; a sandbox_world-anchored version of this test would silently start
    # failing the moment any unrelated session runs `make world-resolve
    # WORLD=sandbox_world`.
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state1, _report = WorldCompiler.compile(spec, seed=42)
    state2, _report = WorldCompiler.compile(spec, seed=137)

    assert state1.terrain == state2.terrain

    h1 = normalize_histogram(compute_terrain_histogram(state1.terrain))
    h2 = normalize_histogram(compute_terrain_histogram(state2.terrain))

    assert total_variation_distance(h1, h2) == 0.0


def test_variants_module_does_not_encode_same_spec_seed_variance_as_a_signal():
    tree = ast.parse(_VARIANTS_MODULE_PATH.read_text())

    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "total_variation_distance":
            found = True
            arg_names = [arg.arg for arg in node.args.args]
            assert arg_names == ["h1", "h2"], (
                f"total_variation_distance must take exactly (h1, h2), got {arg_names}"
            )
    assert found, "total_variation_distance must be defined in variants.py"


def test_compute_terrain_histogram_is_reused_not_reimplemented():
    tree = ast.parse(_VARIANTS_MODULE_PATH.read_text())

    reused = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.rendering.density":
            imported_names = [alias.name for alias in node.names]
            if "compute_terrain_histogram" in imported_names:
                reused = True
    assert reused, "variants.py must import compute_terrain_histogram from density.py"

    source = _VARIANTS_MODULE_PATH.read_text()
    assert "histogram.get(tval, 0) + 1" not in source, (
        "variants.py must not reimplement density.py's terrain-counting loop"
    )


def test_normalize_histogram_converts_counts_to_proportions_summing_to_one():
    raw = {"PLAIN": 3, "FOREST": 1}

    result = normalize_histogram(raw)

    assert result == {"PLAIN": 0.75, "FOREST": 0.25}
    assert abs(sum(result.values()) - 1.0) < 1e-9

    assert normalize_histogram({}) == {}


def test_trail_activity_near_zero_for_stuck_pattern():
    # sample_every=10 over total_ticks=100 yields only 10 recorded position samples,
    # but the correct denominator is ticks_sampled=100 (total_ticks), not len(trail)=10
    # -- see compute_trail_activity's docstring on why using the sample count instead
    # would silently produce a materially different, non-anchor-matching ratio.
    sample_every = 10
    total_ticks = 100
    recorded_samples = total_ticks // sample_every
    assert recorded_samples == 10

    result = compute_trail_activity(unique_tiles_visited=2, ticks_sampled=total_ticks)

    assert result == 0.02
    assert 0.0 <= result <= 0.03


def test_trail_activity_materially_higher_for_moving_pattern():
    stuck = compute_trail_activity(unique_tiles_visited=2, ticks_sampled=100)
    moving = compute_trail_activity(unique_tiles_visited=60, ticks_sampled=100)

    assert moving == 0.6
    assert moving >= stuck * 10


def test_select_trail_entity_is_deterministic_per_world_and_seed():
    entities = {
        1: _entity(1, (0.0, 0.0)),
        2: _entity(2, (1.0, 0.0)),
        3: _entity(3, (3.0, 0.0)),
    }

    first = select_trail_entity("dungeon_crawl", 42, entities)
    second = select_trail_entity("dungeon_crawl", 42, entities)
    assert first == second

    other_seed = select_trail_entity("dungeon_crawl", 137, entities)
    assert other_seed in (1, 2, 3)

    reversed_entities = dict(reversed(list(entities.items())))
    assert select_trail_entity("dungeon_crawl", 42, reversed_entities) == first


def test_select_trail_entity_only_considers_active_entities():
    entities = {
        1: _entity(1, (0.0, 0.0), active=True),
        2: _entity(2, (1.0, 0.0), active=False),
        3: _entity(3, (2.0, 0.0), active=True),
        4: _entity(4, (3.0, 0.0), active=False),
    }

    for seed in range(50):
        result = select_trail_entity("dungeon_crawl", seed, entities)
        assert result in (1, 3)

    with_no_active = {1: _entity(1, (0.0, 0.0), active=False)}
    try:
        select_trail_entity("dungeon_crawl", 42, with_no_active)
        assert False, "expected ValueError when no active entities exist"
    except ValueError:
        pass


def test_variants_module_has_zero_image_or_render_dependency():
    tree = ast.parse(_VARIANTS_MODULE_PATH.read_text())
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
                f"variants.py must not import {name} (image/render dependency)"
            )


def test_variants_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline():
    tree = ast.parse(_VARIANTS_MODULE_PATH.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            base_names = [
                base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                for base in node.bases
            ]
            assert "PillarScorer" not in base_names, "variants.py must not subclass PillarScorer"
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "simulation_quality" not in name, f"variants.py must not import {name}"
            assert "observability.events" not in name, f"variants.py must not import {name}"


def test_does_not_mutate_authoritative_state():
    h1 = {"A": 0.6, "B": 0.4}
    h2 = {"A": 0.4, "B": 0.6}
    h1_before = dict(h1)
    h2_before = dict(h2)

    raw = {"PLAIN": 3, "FOREST": 1}
    raw_before = dict(raw)

    entities = {
        1: _entity(1, (0.0, 0.0)),
        2: _entity(2, (1.0, 0.0)),
    }
    entities_before = dict(entities)

    tvd_1 = total_variation_distance(h1, h2)
    tvd_2 = total_variation_distance(h1, h2)
    norm_1 = normalize_histogram(raw)
    norm_2 = normalize_histogram(raw)
    activity_1 = compute_trail_activity(2, 100)
    activity_2 = compute_trail_activity(2, 100)
    selected_1 = select_trail_entity("dungeon_crawl", 42, entities)
    selected_2 = select_trail_entity("dungeon_crawl", 42, entities)

    assert tvd_1 == tvd_2
    assert norm_1 == norm_2
    assert activity_1 == activity_2
    assert selected_1 == selected_2
    assert h1 == h1_before
    assert h2 == h2_before
    assert raw == raw_before
    assert entities == entities_before
