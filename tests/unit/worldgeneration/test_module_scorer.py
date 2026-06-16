# Compliance IDs: WORLD-GEN-TEST-SCORER
"""
Unit tests for ModuleScorer — intent-driven module fitness scoring.

All tests use lightweight stubs: WorldModuleSpec instances constructed
directly with minimal required fields, no YAML loading.
"""
from __future__ import annotations

import pytest
from src.worldgeneration.schema import GenerationIntentSpec
from src.worldgeneration.scorer import ModuleScore, ModuleScorer
from src.worldmodules.schema import WorldModuleSpec


# ---------------------------------------------------------------------------
# Fixtures — reusable stub modules
# ---------------------------------------------------------------------------

def _make_intent(**kwargs) -> GenerationIntentSpec:
    defaults = dict(
        generation_id="test-gen",
        seed=42,
    )
    defaults.update(kwargs)
    return GenerationIntentSpec(**defaults)


def _make_module(module_id: str, module_type: str, **kwargs) -> WorldModuleSpec:
    defaults = dict(
        display_name=module_id.replace("_", " ").title(),
    )
    defaults.update(kwargs)
    return WorldModuleSpec(module_id=module_id, module_type=module_type, **defaults)


@pytest.fixture
def conflict_module() -> WorldModuleSpec:
    return _make_module(
        "goblin_camp",
        "conflict",
        observability_tags=["hostile", "conflict"],
    )


@pytest.fixture
def danger_tagged_module() -> WorldModuleSpec:
    return _make_module(
        "undead_battlefield",
        "ecology",
        observability_tags=["danger_zone", "hostile"],
    )


@pytest.fixture
def settlement_module() -> WorldModuleSpec:
    return _make_module(
        "frontier_village_core",
        "settlement",
    )


@pytest.fixture
def terrain_module() -> WorldModuleSpec:
    return _make_module(
        "highland_terrain",
        "terrain",
    )


@pytest.fixture
def economy_module() -> WorldModuleSpec:
    return _make_module(
        "trade_post",
        "economy",
    )


@pytest.fixture
def population_module() -> WorldModuleSpec:
    return _make_module(
        "nomad_camp",
        "population",
    )


# ---------------------------------------------------------------------------
# Test 1: danger_level=3.0 — conflict/danger modules score higher
# ---------------------------------------------------------------------------

def test_danger_level_conflict_scores_higher(
    conflict_module, danger_tagged_module, settlement_module
):
    """Conflict and danger-tagged modules must outscore settlement when danger_level=3.0."""
    intent = _make_intent(danger_level=3.0, settlement_style="scattered")
    modules = [conflict_module, danger_tagged_module, settlement_module]

    scores = ModuleScorer.score(intent, modules)

    conflict_score = scores["goblin_camp"].score
    danger_score = scores["undead_battlefield"].score
    village_score = scores["frontier_village_core"].score

    assert conflict_score > village_score, (
        f"goblin_camp ({conflict_score}) should outscore frontier_village_core ({village_score})"
    )
    assert danger_score > village_score, (
        f"undead_battlefield ({danger_score}) should outscore frontier_village_core ({village_score})"
    )

    # Verify reasons mention the danger dimension
    conflict_reasons = " ".join(scores["goblin_camp"].reasons)
    assert "danger_level=3.0" in conflict_reasons, (
        f"Expected danger_level mention in reasons: {scores['goblin_camp'].reasons}"
    )
    danger_reasons = " ".join(scores["undead_battlefield"].reasons)
    assert "danger_level=3.0" in danger_reasons, (
        f"Expected danger_level mention in reasons: {scores['undead_battlefield'].reasons}"
    )


# ---------------------------------------------------------------------------
# Test 2: settlement_style="none" penalises settlement modules
# ---------------------------------------------------------------------------

def test_settlement_style_none_penalises_settlement(settlement_module, terrain_module):
    """settlement_style=none must give settlement modules a near-zero score."""
    intent = _make_intent(settlement_style="none", danger_level=0.0, population_scale=0.0)
    modules = [settlement_module, terrain_module]

    scores = ModuleScorer.score(intent, modules)

    village_score = scores["frontier_village_core"].score
    village_reasons = " ".join(scores["frontier_village_core"].reasons)

    assert village_score < 0.35, (
        f"Settlement module score ({village_score}) should be near 0 when settlement_style=none"
    )
    assert "penalises settlement type" in village_reasons, (
        f"Expected 'penalises settlement type' in reasons: {scores['frontier_village_core'].reasons}"
    )


# ---------------------------------------------------------------------------
# Test 3: required_modules always score 1.0
# ---------------------------------------------------------------------------

def test_required_modules_always_score_one(settlement_module, conflict_module):
    """Modules listed in required_modules must receive score=1.0 and reasons=['required by intent']."""
    intent = _make_intent(required_modules=["frontier_village_core"])
    modules = [settlement_module, conflict_module]

    scores = ModuleScorer.score(intent, modules)

    required_score = scores["frontier_village_core"]
    assert required_score.score == 1.0, (
        f"Required module score must be 1.0, got {required_score.score}"
    )
    assert required_score.reasons == ["required by intent"], (
        f"Required module reasons must be ['required by intent'], got {required_score.reasons}"
    )


# ---------------------------------------------------------------------------
# Test 4: all scores in [0.0, 1.0]
# ---------------------------------------------------------------------------

def test_all_scores_in_range(
    conflict_module, danger_tagged_module, settlement_module,
    terrain_module, economy_module, population_module
):
    """All ModuleScore.score values must be in [0.0, 1.0]."""
    intent = _make_intent(
        danger_level=4.5,
        settlement_style="dense",
        resource_density=0.9,
        population_scale=1.5,
    )
    modules = [
        conflict_module, danger_tagged_module, settlement_module,
        terrain_module, economy_module, population_module,
    ]

    scores = ModuleScorer.score(intent, modules)

    for module_id, ms in scores.items():
        assert 0.0 <= ms.score <= 1.0, (
            f"Score for {module_id} ({ms.score}) is outside [0.0, 1.0]"
        )


# ---------------------------------------------------------------------------
# Test 5: determinism — identical inputs produce identical outputs
# ---------------------------------------------------------------------------

def test_determinism(
    conflict_module, settlement_module, terrain_module
):
    """Calling score() twice with same inputs must return identical results."""
    intent = _make_intent(danger_level=2.0, settlement_style="scattered")
    modules = [conflict_module, settlement_module, terrain_module]

    scores_a = ModuleScorer.score(intent, modules)
    scores_b = ModuleScorer.score(intent, modules)

    for module_id in scores_a:
        a = scores_a[module_id]
        b = scores_b[module_id]
        assert a.score == b.score, f"{module_id}: score differs between calls"
        assert a.reasons == b.reasons, f"{module_id}: reasons differ between calls"
        assert a.dimensions == b.dimensions, f"{module_id}: dimensions differ between calls"


# ---------------------------------------------------------------------------
# Test 6: reasons is non-empty for every module
# ---------------------------------------------------------------------------

def test_reasons_non_empty_for_all(
    conflict_module, danger_tagged_module, settlement_module,
    terrain_module, economy_module, population_module
):
    """Every returned ModuleScore must have a non-empty reasons list."""
    intent = _make_intent(danger_level=1.0)
    modules = [
        conflict_module, danger_tagged_module, settlement_module,
        terrain_module, economy_module, population_module,
    ]

    scores = ModuleScorer.score(intent, modules)

    for module_id, ms in scores.items():
        assert ms.reasons, f"Module {module_id} has empty reasons list"
        assert len(ms.reasons) > 0, f"Module {module_id} has zero reasons"


# ---------------------------------------------------------------------------
# Test 7: dimensions dict has at least one key per module
# ---------------------------------------------------------------------------

def test_dimensions_has_at_least_one_key(
    conflict_module, settlement_module, terrain_module
):
    """Every ModuleScore.dimensions must have at least one key."""
    intent = _make_intent(danger_level=2.0)
    modules = [conflict_module, settlement_module, terrain_module]

    scores = ModuleScorer.score(intent, modules)

    for module_id, ms in scores.items():
        assert ms.dimensions, f"Module {module_id} has empty dimensions dict"
        assert len(ms.dimensions) >= 1, (
            f"Module {module_id} dimensions has 0 keys: {ms.dimensions}"
        )
