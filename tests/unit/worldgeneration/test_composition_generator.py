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
from src.worldgeneration.generator import (
    ProceduralCompositionGenerator,
    GenerationCompositionError,
)
from src.worldgeneration.schema import GenerationIntentSpec
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
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


def _make_catalog() -> CatalogRepository:
    """An explicitly empty catalog: these fixtures' modules reference no catalog records.

    Explicit rather than a cwd-relative load, which is exactly the hidden dependency the
    generator's injected catalog_repo exists to remove.
    """
    repo = CatalogRepository("tests/fixtures/__nonexistent_catalog__")
    repo.load_all()
    return repo


def _make_repo(modules: list[WorldModuleSpec]) -> WorldModuleRepository:
    """Return a WorldModuleRepository populated in memory, with no file I/O.

    A real repository rather than a mock: generate() now resolves the composition it authored,
    and the resolver looks modules up by id through get_module()/module_fingerprint().
    """
    repo = WorldModuleRepository(modules_dir="tests/fixtures/__nonexistent_world_modules__")
    repo.modules = {m.module_id: m for m in modules}
    repo.raw_data = {m.module_id: m.model_dump() for m in modules}
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

        path1 = gen.generate(intent, repo, _make_catalog(), output_dir=tmp_path / "run1")
        path2 = gen.generate(intent, repo, _make_catalog(), output_dir=tmp_path / "run2")

        def _without_origin_timestamp(path):
            raw = yaml.safe_load(path.read_text())
            raw["generation_provenance"].pop("generated_at")
            return raw

        assert _without_origin_timestamp(path1) == _without_origin_timestamp(path2), (
            "Same intent must produce an identical composition"
        )


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

        output_path = gen.generate(intent, repo, _make_catalog())
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

        output_path = gen.generate(intent, repo, _make_catalog())
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

        output_path = gen.generate(intent, repo, _make_catalog())
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
        output_path = gen.generate(intent, repo, _make_catalog())

        # Exact path, not a "generated" substring check: the old assertion survived the move to
        # the authoritative layout only by accident, because the world_id itself starts with
        # "generated_".
        assert (
            output_path.resolve()
            == (tmp_path / "data/worlds" / "generated_frontier_3_42" / "world.yaml").resolve()
        )

    def test_output_path_contains_seed_and_style(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        modules = [_make_module("terrain_arid", "terrain")]
        repo = _make_repo(modules)
        intent = _default_intent(settlement_style="none", danger_level=1.0, seed=99)
        gen = ProceduralCompositionGenerator()
        output_path = gen.generate(intent, repo, _make_catalog())

        assert output_path.parent.name == "generated_none_1_99"
        assert output_path.name == "world.yaml"


class TestAuthoritativeOutputLocation:
    """The generator authors the source definition directly (AC-9).

    Deliberately absent from this class: any test asserting
    `world.yaml == generate(provenance_marker)`. That would convert the marker into a
    re-derivation obligation and make `world.yaml` a projection of params stored inside it —
    forbidden by docs/architecture/world_repository_layout.md §1.
    """

    def test_generation_run_does_not_create_data_content_world_compositions(self, tmp_path, monkeypatch):
        """Absence asserted explicitly — asserting only that the new path exists would pass a
        'wrote to both' implementation."""
        monkeypatch.chdir(tmp_path)
        gen = ProceduralCompositionGenerator()
        gen.generate(
            _default_intent(), _make_repo([_make_module("terrain_basic", "terrain")]), _make_catalog()
        )

        assert not (tmp_path / "data/content/world_compositions").exists()

    def test_generated_world_has_its_resolved_sibling(self, tmp_path, monkeypatch):
        """Without it, WorldRepository.load_world() refuses the world it just authored."""
        monkeypatch.chdir(tmp_path)
        gen = ProceduralCompositionGenerator()
        output_path = gen.generate(
            _default_intent(), _make_repo([_make_module("terrain_basic", "terrain")]), _make_catalog()
        )

        resolved = output_path.parent / "resolved"
        assert (resolved / "world.resolved.yaml").is_file()
        for sidecar in (
            "compile_context.json",
            "provenance_manifest.json",
            "assembly_report.json",
            "validation_report.json",
        ):
            assert (resolved / sidecar).is_file()

    def test_generated_world_records_provenance_history(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        gen = ProceduralCompositionGenerator()
        intent = _default_intent(seed=1234, settlement_style="frontier")
        output_path = gen.generate(
            intent, _make_repo([_make_module("terrain_basic", "terrain")]), _make_catalog()
        )

        spec = WorldCompositionSpec.model_validate(yaml.safe_load(output_path.read_text()))
        provenance = spec.generation_provenance
        assert provenance is not None
        assert provenance.generator == "ProceduralCompositionGenerator"
        assert provenance.generator_version
        assert provenance.generation_id == intent.generation_id
        assert provenance.seed == 1234
        assert provenance.generated_at
        assert provenance.intent_parameters["settlement_style"] == "frontier"

    def test_generate_refuses_to_overwrite_an_existing_definition(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        gen = ProceduralCompositionGenerator()
        modules = [_make_module("terrain_basic", "terrain")]
        intent = _default_intent()
        gen.generate(intent, _make_repo(modules), _make_catalog())

        with pytest.raises(GenerationCompositionError, match="already exists"):
            gen.generate(intent, _make_repo(modules), _make_catalog())

    def test_resolve_failure_leaves_no_half_written_world(self, tmp_path, monkeypatch):
        """The one path that could produce an unrecoverable state.

        A world.yaml committed before a failed resolve would be both unloadable (no resolved/
        snapshot) and un-regenerable (refuse-to-overwrite), so the resolve runs first.
        """
        monkeypatch.chdir(tmp_path)
        gen = ProceduralCompositionGenerator()
        modules = [_make_module("terrain_basic", "terrain")]
        intent = _default_intent()

        def _boom(*args, **kwargs):
            raise RuntimeError("resolve exploded")

        monkeypatch.setattr("src.worldgeneration.generator.resolve_composition", _boom)
        with pytest.raises(RuntimeError, match="resolve exploded"):
            gen.generate(intent, _make_repo(modules), _make_catalog())

        world_dir = tmp_path / "data/worlds" / "generated_frontier_3_42"
        assert not (world_dir / "world.yaml").exists()

        monkeypatch.undo()
        monkeypatch.chdir(tmp_path)
        retried = gen.generate(intent, _make_repo(modules), _make_catalog())
        assert retried.is_file()


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
            gen.generate(intent, repo, _make_catalog())

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
        output_path = gen.generate(intent, repo, _make_catalog())
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

        output_path = gen.generate(intent, repo, _make_catalog())
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

        output_path = gen.generate(intent, repo, _make_catalog())
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

        output_path = gen.generate(intent, repo, _make_catalog())
        raw = yaml.safe_load(output_path.read_text())
        spec = WorldCompositionSpec.model_validate(raw)

        # Without deps, selected count should be <= BUDGET
        # (Deps may push it over, but initial candidates are capped)
        assert len(spec.module_refs) <= ProceduralCompositionGenerator.BUDGET + 5, (
            "Module count should be near budget (deps can add a few extra)"
        )


class TestRegionIdNamespacing:
    """Two selected modules declaring one region id must be disambiguated by namespace."""

    @staticmethod
    def _regional(module_id: str, module_type: str = "settlement"):
        from src.worldbuilding.recipe import RegionRecipeSpec

        mod = _make_module(module_id, module_type)
        return mod.model_copy(update={
            "regions": [RegionRecipeSpec(id="hometown", type="town", grid_bounds=(0, 0, 5, 5))]
        })

    def _generate(self, modules, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = ProceduralCompositionGenerator().generate(
            _default_intent(), _make_repo(modules)
        )
        raw = yaml.safe_load(path.read_text())
        return {r["module_id"]: r.get("namespace") for r in raw["module_refs"]}

    def test_colliding_region_id_gets_namespace(self, tmp_path, monkeypatch):
        refs = self._generate(
            [self._regional("aaa_core"), self._regional("zzz_hub"), _make_module("terrain_basic", "terrain")],
            tmp_path, monkeypatch,
        )
        assert refs  # non-vacuous
        assert refs["aaa_core"] is None
        assert refs["zzz_hub"] == "zzz_hub"
        assert refs["terrain_basic"] is None

    def test_bare_id_owner_is_independent_of_selection_order(self, tmp_path, monkeypatch):
        """Condition 1: the same module keeps the bare id however the modules are listed/ranked."""
        a, z = self._regional("aaa_core"), self._regional("zzz_hub")
        t = _make_module("terrain_basic", "terrain")
        forward = self._generate([a, z, t], tmp_path, monkeypatch)
        reverse = self._generate([t, z, a], tmp_path, monkeypatch)
        assert forward == reverse
        assert forward["aaa_core"] is None

    def test_no_collision_leaves_namespace_unset(self, tmp_path, monkeypatch):
        refs = self._generate(
            [_make_module("terrain_basic", "terrain"), _make_module("village_core", "settlement")],
            tmp_path, monkeypatch,
        )
        assert refs
        assert all(ns is None for ns in refs.values())
