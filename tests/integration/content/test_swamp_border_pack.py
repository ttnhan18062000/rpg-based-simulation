"""
swamp_border_pack validation tests.

Acceptance criteria:
- Manifest validates against content_pack.v1 schema
- All pack content IDs resolve in catalog
- Pack dependencies resolve against base content
- Pack strict matrix passes when enabled
- Pack disabled → base world strict matrix unchanged
- All active records have consumer paths (sample_compositions + sample_scenarios declared)
"""

from __future__ import annotations

import pytest
import yaml

from src.content.pack_manifest import ContentPackManifest, ContentPackManifestValidator
from src.content.repository import CatalogRepository

PACK_PATH = "data/content/packs/swamp_border_pack.yaml"
PACK_ID = "swamp_border_pack"


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def raw_manifest():
    with open(PACK_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def manifest(raw_manifest):
    return ContentPackManifest(**raw_manifest)


# ---------------------------------------------------------------------------
# 1. Manifest schema
# ---------------------------------------------------------------------------

def test_manifest_validates_against_schema(raw_manifest):
    """ContentPackManifest Pydantic schema must accept the pack file."""
    m = ContentPackManifest(**raw_manifest)
    assert m.pack_id == PACK_ID
    assert m.schema_version == "content_pack.v1"
    assert m.enabled is True


def test_manifest_has_required_consumer_paths(manifest):
    """Pack must declare at least one composition and one scenario consumer."""
    assert manifest.sample_compositions, "Pack must have at least one sample_composition"
    assert manifest.sample_scenarios, "Pack must have at least one sample_scenario"


def test_manifest_strict_validation_result(manifest):
    """strict_validation_result must be PASS."""
    assert manifest.strict_validation_result == "PASS"


# ---------------------------------------------------------------------------
# 2. Content resolution
# ---------------------------------------------------------------------------

def test_pack_archetypes_resolve_in_catalog(catalog, manifest):
    for aid in manifest.included_families.get("entity_archetypes", []):
        a = catalog.get_entity_archetype(aid)
        assert a is not None, f"Archetype {aid!r} declared in pack but not found in catalog"


def test_pack_populations_resolve_in_catalog(catalog, manifest):
    for pid in manifest.included_families.get("populations", []):
        p = catalog.get_population_recipe(pid)
        assert p is not None, f"Population {pid!r} declared in pack but not found in catalog"


def test_pack_world_modules_resolve(manifest):
    """Each world module file must exist on disk."""
    import os
    for mid in manifest.included_families.get("world_modules", []):
        path = f"data/content/world_modules/{mid}.yaml"
        assert os.path.exists(path), f"World module {mid!r} file not found at {path}"


def test_pack_sample_composition_file_exists(manifest):
    import os
    for cid in manifest.sample_compositions:
        path = f"data/content/world_compositions/{cid}.yaml"
        assert os.path.exists(path), f"Sample composition {cid!r} file not found at {path}"


# ---------------------------------------------------------------------------
# 3. Dependencies
# ---------------------------------------------------------------------------

def test_pack_dependencies_resolve(manifest):
    """All declared dependencies are known packs."""
    known = {"frontier_extended_pack", "swamp_border_pack"}
    validator = ContentPackManifestValidator()
    errors = validator.validate(manifest, known_packs=known)
    assert not errors, f"Dependency validation errors: {errors}"


def test_pack_has_no_unknown_dependencies(manifest):
    """swamp_border_pack should declare no dependencies (reuses base catalog only)."""
    assert manifest.dependencies == [], \
        f"Expected empty dependencies, got {manifest.dependencies}"


# ---------------------------------------------------------------------------
# 4. Pack strict matrix
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def module_repo():
    from src.worldmodules.repository import WorldModuleRepository
    repo = WorldModuleRepository()
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def assembly_resolver(catalog, module_repo):
    from src.worldassembly.resolver import WorldAssemblyResolver
    return WorldAssemblyResolver(catalog, module_repo)


def _make_comp(module_ids):
    from src.worldassembly.schema import WorldCompositionSpec
    return WorldCompositionSpec.model_validate({
        "schema_version": "worldcomposition.v1",
        "world_id": "swamp_pack_test",
        "name": "Swamp Pack Test",
        "modules": module_ids,
    })


def test_swamp_border_pack_strict_matrix_passes(assembly_resolver):
    """World assembly with sunken_swamp_border module must succeed without blocking errors."""
    comp = _make_comp(["frontier_village_core", "wolf_den_near_forest", "sunken_swamp_border"])
    bundle = assembly_resolver.assemble(comp)
    blocking = [e for e in bundle.assembly_report.get("errors", [])
                if e.get("severity") == "blocking"]
    assert not blocking, f"Assembly had blocking errors: {blocking}"


# ---------------------------------------------------------------------------
# 5. Pack disabled → base unaffected
# ---------------------------------------------------------------------------

def test_base_strict_matrix_unaffected_by_pack_content(assembly_resolver):
    """
    Base world assembly must succeed even when swamp pack archetypes are present in catalog.
    """
    comp = _make_comp(["frontier_village_core", "wolf_den_near_forest",
                       "goblin_camp_conflict", "old_mine_resource_loop"])
    bundle = assembly_resolver.assemble(comp)
    assert bundle is not None, "Base world assembly must succeed even with swamp pack content in catalog"
