# Compliance IDs: WORLD-ASM-TEST
import pytest
import json
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec, ProvenanceManifest, ProvenanceRecord
from src.worldassembly.resolver import WorldAssemblyResolver


@pytest.fixture
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository("data/world_modules")
    mod.load_all()
    return cat, mod


def test_provenance_manifest_attributes(repos):
    """Verify that ProvenanceManifest contains all 11 required attributes and maps element types correctly."""
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="resolved_asm_test",
        name="Resolved Asm Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
            ModuleRefSpec(module_id="standard_villagers", enabled=True, order=1)
        ]
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    manifest = bundle.provenance_manifest

    # Assert 11 required attributes are present
    assert hasattr(manifest, "manifest_id")
    assert hasattr(manifest, "world_id")
    assert hasattr(manifest, "source_schema_version")
    assert hasattr(manifest, "catalog_fingerprint")
    assert hasattr(manifest, "module_fingerprints")
    assert hasattr(manifest, "composition_fingerprint")
    assert hasattr(manifest, "resolver_version")
    assert hasattr(manifest, "generator_version")
    assert hasattr(manifest, "seed")
    assert hasattr(manifest, "created_at")
    assert hasattr(manifest, "records")

    # Assert basic contents
    assert manifest.world_id == "resolved_asm_test"
    assert manifest.source_schema_version == "provenancemanifest.v1"
    assert manifest.resolver_version == "1.0.0"

    # Assert records mapping matches the merged components
    assert "town_center" in manifest.records
    region_record = manifest.records["town_center"]
    assert region_record.element_type == "region"
    assert region_record.source_module == "plains_layout"

    assert "pop_0" in manifest.records
    pop_record = manifest.records["pop_0"]
    assert pop_record.element_type == "population"
    assert pop_record.source_module == "standard_villagers"


def test_provenance_determinism(repos):
    """Verify that compiling the same composition twice yields 100% byte-identical, deterministic manifests."""
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="resolved_asm_test",
        name="Resolved Asm Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
            ModuleRefSpec(module_id="standard_villagers", enabled=True, order=1)
        ]
    )

    resolver = WorldAssemblyResolver(cat, mod)
    
    # Compile 1
    bundle1 = resolver.assemble(composition)
    dump1 = json.dumps(bundle1.provenance_manifest.model_dump(), sort_keys=True)

    # Compile 2
    bundle2 = resolver.assemble(composition)
    dump2 = json.dumps(bundle2.provenance_manifest.model_dump(), sort_keys=True)

    # Byte-identical determinism assertion
    assert dump1 == dump2
