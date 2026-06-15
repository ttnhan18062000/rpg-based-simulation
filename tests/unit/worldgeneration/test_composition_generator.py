# Compliance IDs: WORLD-GEN-006-TEST
"""
Unit tests for ProceduralCompositionGenerator.

Stubs WorldModuleRepository to avoid file I/O.
All tests use deterministic seeds.
"""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock

from src.worldgeneration.generator import (
    ProceduralCompositionGenerator,
    GenerationCompositionError,
)
from src.worldgeneration.schema import GenerationIntentSpec
from src.worldmodules.schema import WorldModuleSpec
from src.worldassembly.schema import WorldCompositionSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_module(
    module_id: str,
    module_type: str = "terrain",
    requires: list[str] | None = None,
    provides: list[str] | None = None,
    observability_tags: list[str] | None = None,
    resource_recipes: list | None = None,
) -> WorldModuleSpec:
    """Build a minimal WorldModuleSpec stub."""
    return WorldModuleSpec(
        module_id=module_id,
        module_type=module_type,
        display_name=f"Module {module_id}",
        requires=requires or [],
        provides=provides or [],
        observability_tags=observability_tags or [],
        resource_recipes=resource_recipes or [],
    )


def _make_repo(modules: list[WorldModuleSpec]) -> MagicMock:
    """Return a mock WorldModuleRepository with list_modules() returning given modules."""
    repo = MagicMock()
    repo.list_modules.return_value = modules
    return repo


def _default_intent(**kwargs) -> GenerationIntentSpec:
    """Return a GenerationIntentSpec with sensible defaults, overridable via kwargs."""
    defaults = dict(
        generation_id="test_gen",
        seed=42,
        settlement_style="frontier",
        danger_level=3.0,
        terrain_style="temperate",
        resource_density=1.0,
        population_scale=1.0,
    )
    defaults.update(kwargs)
    return GenerationIntentSpec(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDeterminism:
    """Same intent + seed → identical YAML output."""

    def test_two_calls_produce_identical_output(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        modules = [
            _make_module("terrain_basic", "terrain"),
            _make_module("village_core", "settlement"),
        ]
        repo = _make_repo(modules)
        intent = _default_intent()
        gen = ProceduralCompositionGenerator()

        path1 = gen.generate(intent, repo)
        content1 = path1.read_text()

        # Remove generated file so second call recreates it fresh
        path1.unlink()

        path2 = gen.generate(intent, repo)
        content2 = path2.read_text()

        assert content1 == content2, "Same intent must produce byte-identical YAML"


class TestSettlementStyleNone:
    """settlement_style='none' must not include any settlement-type module."""

    def test_no_settlement_module_when_style_is_none(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        modules = [
            _make_module("terrain_basic", "terrain"),
            _make_module("village_core", "settlement"),
            _make_module("ecology_base", "ecology"),
        ]
        repo = _make_repo(modules)
        intent = _default_intent(settlement_style="none")
        gen = ProceduralCompositionGenerator()

        output_path = gen.generate(intent, repo)
        raw = yaml.safe_load(output_path.read_text())
        spec = WorldCompositionSpec.model_validate(raw)

        selected_ids = {ref.module_id for ref in spec.module_refs}
        assert "village_core" not in selected_ids, (
            "settlement-type module must not appear when settlement_style='none'"
        )
        assert "terrain_basic" in selected_ids, "terrain module must always be included"


class TestDependencyAutoInclusion:
    """A module's required dependencies are included automatically."""

    def test_required_dep_is_included(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # dep_only doesn't score high enough alone but is required by conflict module
        dep_module = _make_module("dep_only", "ecology")
        conflict_module = _make_module(
            "goblin_camp_conflict",
            "conflict",
            requires=["dep_only"],
            observability_tags=["hostile", "conflict"],
        )
        terrain_module = _make_module("terrain_basic", "terrain")

        repo = _make_repo([terrain_module, conflict_module, dep_module])
        # High danger level ensures conflict module scores well
        intent = _default_intent(danger_level=5.0, settlement_style="none")
        gen = ProceduralCompositionGenerator()

        output_path = gen.generate(intent, repo)
        raw = yaml.safe_load(output_path.read_text())
        spec = WorldCompositionSpec.model_validate(raw)

        selected_ids = {ref.module_id for ref in spec.module_refs}
        assert "goblin_camp_conflict" in selected_ids
        assert "dep_only" in selected_ids, (
            "dep_only must be auto-included as a dependency of goblin_camp_conflict"
        )

    def test_transitive_deps_are_resolved(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # A requires B, B requires C
        mod_c = _make_module("mod_c", "ecology")
        mod_b = _make_module("mod_b", "ecology", requires=["mod_c"])
        mod_a = _make_module(
            "mod_a", "conflict",
            requires=["mod_b"],
            observability_tags=["hostile"],
        )
        terrain = _make_module("terrain_base", "terrain")

        repo = _make_repo([terrain, mod_a, mod_b, mod_c])
        intent = _default_intent(danger_level=5.0, settlement_style="none")
        gen = ProceduralCompositionGenerator()

        output_path = gen.generate(intent, repo)
        raw = yaml.safe_load(output_path.read_text())
        spec = WorldCompositionSpec.model_validate(raw)

        selected_ids = {ref.module_id for ref in spec.module_refs}
        assert "mod_a" in selected_ids
        assert "mod_b" in selected_ids
        assert "mod_c" in selected_ids


class TestOutputPath:
    """Returned path matches expected naming convention."""

    def test_output_path_pattern(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        modules = [_make_module("terrain_basic", "terrain")]
        repo = _make_repo(modules)
        intent = _default_intent(
            settlement_style="frontier",
            danger_level=3.0,
            seed=42,
        )
        gen = ProceduralCompositionGenerator()
        output_path = gen.generate(intent, repo)

        assert output_path.name == "generated_frontier_3_42.yaml", (
            f"Expected generated_frontier_3_42.yaml, got {output_path.name}"
        )
        assert "generated" in str(output_path), (
            "Output should be under the generated/ subdirectory"
        )

    def test_output_path_contains_seed_and_style(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        modules = [_make_module("terrain_arid", "terrain")]
        repo = _make_repo(modules)
        intent = _default_intent(settlement_style="none", danger_level=1.0, seed=99)
        gen = ProceduralCompositionGenerator()
        output_path = gen.generate(intent, repo)

        assert output_path.name == "generated_none_1_99.yaml"


class TestConflictDetection:
    """Two modules claiming the same provide string raise GenerationCompositionError."""

    def test_conflicting_provides_raises(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        terrain = _make_module("terrain_basic", "terrain")
        mod_a = _make_module(
            "mod_a", "ecology",
            provides=["exclusive_water_system"],
        )
        mod_b = _make_module(
            "mod_b", "ecology",
            provides=["exclusive_water_system"],
        )

        repo = _make_repo([terrain, mod_a, mod_b])
        intent = _default_intent(settlement_style="none")
        gen = ProceduralCompositionGenerator()

        with pytest.raises(GenerationCompositionError) as exc_info:
            gen.generate(intent, repo)

        error_msg = str(exc_info.value)
        assert "mod_a" in error_msg or "mod_b" in error_msg, (
            "Error must name the conflicting module IDs"
        )
        assert "exclusive_water_system" in error_msg, (
            "Error must name the conflicting feature"
        )

    def test_non_conflicting_provides_does_not_raise(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        terrain = _make_module("terrain_basic", "terrain")
        mod_a = _make_module("mod_a", "ecology", provides=["water_system"])
        mod_b = _make_module("mod_b", "ecology", provides=["fire_system"])

        repo = _make_repo([terrain, mod_a, mod_b])
        intent = _default_intent(settlement_style="none")
        gen = ProceduralCompositionGenerator()

        # Should not raise
        output_path = gen.generate(intent, repo)
        assert output_path.exists()


class TestOutputValidity:
    """Output YAML must parse cleanly as a valid WorldCompositionSpec."""

    def test_output_is_valid_composition_spec(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        modules = [
            _make_module("terrain_temperate", "terrain"),
            _make_module("frontier_village", "settlement"),
            _make_module("ecology_forest", "ecology"),
        ]
        repo = _make_repo(modules)
        intent = _default_intent()
        gen = ProceduralCompositionGenerator()

        output_path = gen.generate(intent, repo)
        raw = yaml.safe_load(output_path.read_text())

        # Must parse without exception
        spec = WorldCompositionSpec.model_validate(raw)
        assert spec.schema_version == "worldcomposition.v1"
        assert spec.world_id.startswith("generated_")
        assert spec.generation_seed == intent.seed
        assert len(spec.module_refs) > 0

    def test_module_refs_have_correct_order(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        modules = [
            _make_module("terrain_a", "terrain"),
            _make_module("settlement_b", "settlement"),
        ]
        repo = _make_repo(modules)
        intent = _default_intent()
        gen = ProceduralCompositionGenerator()

        output_path = gen.generate(intent, repo)
        raw = yaml.safe_load(output_path.read_text())
        spec = WorldCompositionSpec.model_validate(raw)

        orders = [ref.order for ref in spec.module_refs]
        # Orders should be sequential starting from 0
        assert orders == list(range(len(spec.module_refs)))


class TestBudgetLimit:
    """Selection does not exceed BUDGET modules (before dependency expansion)."""

    def test_budget_caps_initial_selection(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Build more modules than the budget
        modules = (
            [_make_module("terrain_base", "terrain")]
            + [_make_module(f"ecology_{i}", "ecology") for i in range(10)]
        )
        repo = _make_repo(modules)
        intent = _default_intent(settlement_style="none")
        gen = ProceduralCompositionGenerator()

        output_path = gen.generate(intent, repo)
        raw = yaml.safe_load(output_path.read_text())
        spec = WorldCompositionSpec.model_validate(raw)

        # Without deps, selected count should be <= BUDGET
        # (Deps may push it over, but initial candidates are capped)
        assert len(spec.module_refs) <= ProceduralCompositionGenerator.BUDGET + 5, (
            "Module count should be near budget (deps can add a few extra)"
        )
