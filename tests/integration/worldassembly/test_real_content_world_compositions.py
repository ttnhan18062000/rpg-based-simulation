import os
import pytest
import yaml
from pathlib import Path
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.schema import WorldCompositionSpec, WorldCompositionNormalizer
from src.worldassembly.resolver import WorldAssemblyResolver

pytestmark = pytest.mark.worldassembly


@pytest.fixture(scope="module")
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    
    # Use canonical path
    mod = WorldModuleRepository()
    mod.load_all()
    return cat, mod


def test_real_world_compositions_load_and_validate(repos):
    """Verify that the real composition file loads and passes validation."""
    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    assert comp_path.is_file()

    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Validate with Pydantic model
    spec = WorldCompositionSpec.model_validate(raw)
    assert spec.world_id == "frontier_living_world"
    assert spec.name == "Frontier Living World"


def test_real_world_compositions_normalization(repos):
    """Verify that the real composition normalizes shorthand modules correctly."""
    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    normalized = WorldCompositionNormalizer.normalize(spec)

    assert normalized.world_id == "frontier_living_world"
    # Verify that shorthand 'modules' list is fully converted to module_refs
    assert len(normalized.module_refs) == 6
    for ref in normalized.module_refs:
        assert ref.enabled is True
        assert ref.order == 0


def test_real_world_compositions_assembly(repos):
    """Verify that the real composition resolves and compiles without error."""
    cat, mod = repos
    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(spec)

    assert bundle is not None
    assert bundle.world_spec is not None
    assert bundle.compile_context is not None
    assert bundle.provenance_manifest is not None

    # Verify that regions are merged from modules
    assert len(bundle.world_spec.regions) > 0

    # Verify that default perspectives are present in the composition spec
    assert len(spec.default_perspectives) == 3
    assert "hero_guild_perspective" in spec.default_perspectives


def test_real_world_compositions_determinism_and_provenance(repos):
    """Verify deterministic compilation output, fingerprint stability, and provenance sidecar data."""
    cat, mod = repos
    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    resolver = WorldAssemblyResolver(cat, mod)

    # Perform assembly twice to verify determinism
    bundle1 = resolver.assemble(spec)
    bundle2 = resolver.assemble(spec)

    # Check fingerprint stability
    assert bundle1.provenance_manifest.catalog_fingerprint == bundle2.provenance_manifest.catalog_fingerprint
    assert bundle1.provenance_manifest.composition_fingerprint == bundle2.provenance_manifest.composition_fingerprint
    assert bundle1.provenance_manifest.content_fingerprint == bundle2.provenance_manifest.content_fingerprint
    assert bundle1.provenance_manifest.manifest_id == bundle2.provenance_manifest.manifest_id

    # Check that module fingerprints are resolved and consistent
    assert len(bundle1.provenance_manifest.module_fingerprints) == 6
    assert bundle1.provenance_manifest.module_fingerprints == bundle2.provenance_manifest.module_fingerprints

    # Verify provenance manifest details (records and origins mapped)
    records = bundle1.provenance_manifest.records
    assert len(records) > 0

    # Ensure elements reference their source module
    regions_with_source = [r for r in records.values() if r.element_type == "region"]
    assert len(regions_with_source) > 0
    for r in regions_with_source:
        assert r.source_module is not None

    # Ensure archetype source and population recipe sources are tracked in provenance
    populations = [p for p in records.values() if p.element_type == "population"]
    assert len(populations) > 0
