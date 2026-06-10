"""
Strict world matrix integration tests.

Each row is a cumulative module composition proving the full content pipeline:
  load → validate → normalize → archetype/population resolve → WorldSpec + CompileContext
  → runtime registry seeding → deterministic fingerprint

Pre-assembly tests (load, normalize, fingerprint) always pass.
Full-assembly tests verify the complete pipeline through WorldSpec + CompileContext.

Tests respect the ownership boundary from TCK-20260609-PRESERVE-ASSEMBLY-TESTS:
basic "assembly works" and "catalog loads" behaviors are not duplicated here.
Each row verifies correctness of the content pipeline, not the assembler itself.
"""

import pytest

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
from src.worldassembly.schema import WorldCompositionSpec
from src.worldassembly.resolver import WorldAssemblyResolver
from src.core.registries import seed_phase1_content
from src.core.modes import RuntimeContentMode

# ---------------------------------------------------------------------------
# Matrix definition: each entry is (row_label, cumulative_module_list)
# ---------------------------------------------------------------------------

_MATRIX = [
    ("frontier_only",   ["frontier_village_core"]),
    ("+ wolf_den",      ["frontier_village_core", "wolf_den_near_forest"]),
    ("+ goblin_camp",   ["frontier_village_core", "wolf_den_near_forest", "goblin_camp_conflict"]),
    ("+ old_mine",      ["frontier_village_core", "wolf_den_near_forest", "goblin_camp_conflict",
                         "old_mine_resource_loop"]),
    ("+ bandit_road",   ["frontier_village_core", "wolf_den_near_forest", "goblin_camp_conflict",
                         "old_mine_resource_loop", "bandit_road_trade_pressure"]),
    ("+ undead",        ["frontier_village_core", "wolf_den_near_forest", "goblin_camp_conflict",
                         "old_mine_resource_loop", "bandit_road_trade_pressure", "undead_battlefield"]),
    ("+ moon_cult",     ["frontier_village_core", "wolf_den_near_forest", "goblin_camp_conflict",
                         "old_mine_resource_loop", "bandit_road_trade_pressure", "undead_battlefield",
                         "moon_cult_ruins"]),
    ("+ orc_clan",      ["frontier_village_core", "wolf_den_near_forest", "goblin_camp_conflict",
                         "old_mine_resource_loop", "bandit_road_trade_pressure", "undead_battlefield",
                         "orc_clan_territory"]),
    ("+ forest_warden", ["frontier_village_core", "wolf_den_near_forest", "goblin_camp_conflict",
                         "old_mine_resource_loop", "bandit_road_trade_pressure", "undead_battlefield",
                         "orc_clan_territory", "forest_warden_grove"]),
]

_MATRIX_IDS = [label for label, _ in _MATRIX]

pytestmark = [pytest.mark.worldassembly, pytest.mark.strict_matrix]


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def module_repo():
    repo = WorldModuleRepository()
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def assembly_resolver(catalog, module_repo):
    return WorldAssemblyResolver(catalog, module_repo)


def _make_composition(module_ids: list[str]) -> WorldCompositionSpec:
    return WorldCompositionSpec.model_validate({
        "schema_version": "worldcomposition.v1",
        "world_id": f"matrix_{'_'.join(m.split('_')[0] for m in module_ids)}",
        "name": f"Matrix: {', '.join(module_ids)}",
        "modules": module_ids,
    })


# ---------------------------------------------------------------------------
# Pre-assembly tests: always pass (no assembly required)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label,modules", _MATRIX, ids=_MATRIX_IDS)
def test_each_module_loads_from_repository(module_repo, label, modules):
    """Every module in the row is present in the module repository."""
    for module_id in modules:
        spec = module_repo.get_module(module_id)
        assert spec is not None, f"Module {module_id!r} missing from repository"
        assert spec.module_id == module_id


@pytest.mark.parametrize("label,modules", _MATRIX, ids=_MATRIX_IDS)
def test_each_module_normalizes_without_error(module_repo, label, modules):
    """Every module in the row normalizes to NormalizedWorldModule."""
    for module_id in modules:
        spec = module_repo.get_module(module_id)
        normalized = WorldModuleAuthoringNormalizer.normalize(spec)
        assert normalized.module_id == module_id


@pytest.mark.parametrize("label,modules", _MATRIX, ids=_MATRIX_IDS)
def test_each_module_has_deterministic_fingerprint(module_repo, label, modules):
    """Module fingerprints are stable across two lookups."""
    for module_id in modules:
        fp1 = module_repo.module_fingerprint(module_id)
        fp2 = module_repo.module_fingerprint(module_id)
        assert fp1 is not None and fp1 != "", f"Module {module_id!r} has empty fingerprint"
        assert fp1 == fp2


# ---------------------------------------------------------------------------
# Runtime registry seeding (catalog-level, not assembly-dependent)
# ---------------------------------------------------------------------------

def test_catalog_seeds_runtime_registries(catalog):
    """Seeding runtime registries from the catalog succeeds and populates items/resources."""
    from src.core.registries import ItemRegistry, ResourceRegistry
    seed_phase1_content(catalog, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
    # Verify seeding produced non-empty registries
    assert len(ItemRegistry._items) > 0, "ItemRegistry is empty after seeding"
    assert len(ResourceRegistry._resources) > 0, "ResourceRegistry is empty after seeding"


# ---------------------------------------------------------------------------
# Full-assembly tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label,modules", _MATRIX, ids=_MATRIX_IDS)
def test_row_produces_world_spec(assembly_resolver, label, modules):
    comp = _make_composition(modules)
    bundle = assembly_resolver.assemble(comp)
    assert bundle.world_spec is not None
    assert bundle.world_spec.world_id is not None
    assert len(bundle.world_spec.regions) > 0


@pytest.mark.parametrize("label,modules", _MATRIX, ids=_MATRIX_IDS)
def test_row_produces_compile_context_with_seeded_entities(assembly_resolver, label, modules):
    comp = _make_composition(modules)
    bundle = assembly_resolver.assemble(comp)
    ctx = bundle.compile_context
    assert ctx is not None
    # CompileContext must have at least one entity registered
    assert len(ctx.entities) > 0, "CompileContext has no seeded entity profiles"


@pytest.mark.parametrize("label,modules", _MATRIX, ids=_MATRIX_IDS)
def test_row_assembly_has_no_blocking_errors(assembly_resolver, label, modules):
    comp = _make_composition(modules)
    bundle = assembly_resolver.assemble(comp)
    report = bundle.assembly_report
    assert report["summary"]["status"] == "SUCCESS"
    assert report["blocking_errors"] == []


@pytest.mark.parametrize("label,modules", _MATRIX, ids=_MATRIX_IDS)
def test_row_assembly_is_deterministic(assembly_resolver, label, modules):
    """Assembling the same composition twice must produce the same content fingerprint."""
    comp = _make_composition(modules)
    bundle_a = assembly_resolver.assemble(comp)
    bundle_b = assembly_resolver.assemble(comp)
    assert (
        bundle_a.provenance_manifest.content_fingerprint
        == bundle_b.provenance_manifest.content_fingerprint
    )


@pytest.mark.parametrize("label,modules", _MATRIX, ids=_MATRIX_IDS)
def test_row_no_hidden_legacy_fallback_in_archetype_entities(assembly_resolver, label, modules):
    """Entities that came from archetype resolution must have archetype_id set in profile."""
    comp = _make_composition(modules)
    bundle = assembly_resolver.assemble(comp)
    ctx = bundle.compile_context
    for key, profile in ctx.entities.items():
        if profile.archetype_id is not None:
            assert profile.role_id is not None, (
                f"Entity {key!r} has archetype_id but missing role_id — hidden legacy fallback"
            )
            assert profile.faction_id is not None, (
                f"Entity {key!r} has archetype_id but missing faction_id — hidden legacy fallback"
            )
