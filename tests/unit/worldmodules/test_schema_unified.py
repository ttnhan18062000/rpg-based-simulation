# Compliance IDs: WORLD-MOD-001, WORLD-MOD-002 — schema unification guards
import dataclasses

import pytest
from pydantic import ValidationError

from src.worldmodules.normalizer import NormalizedWorldModule, WorldModuleAuthoringNormalizer
from src.worldmodules.schema import WorldModuleSpec


def _make_minimal(extra: dict | None = None) -> dict:
    base = {
        "module_id": "test_mod",
        "module_type": "terrain",
        "display_name": "Test Module",
    }
    if extra:
        base.update(extra)
    return base


def test_unified_module_accepts_v1_and_v2_fields_together():
    """NT-1: Module with both recipe-style fields and catalog-ref fields normalizes without error."""
    spec = WorldModuleSpec.model_validate(_make_minimal({
        "biomes": ["forest_biome"],
        "ecologies": ["temperate_ecology"],
        "population_recipes": [],
        "resource_recipes": [],
    }))
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)
    assert normalized.module_id == "test_mod"
    assert normalized.biome_refs == ("forest_biome",)
    assert normalized.ecology_refs == ("temperate_ecology",)


def test_module_loads_without_schema_version():
    """NT-2: schema_version omitted entirely — WorldModuleSpec.model_validate() must succeed."""
    data = _make_minimal()
    assert "schema_version" not in data
    spec = WorldModuleSpec.model_validate(data)
    assert spec.module_id == "test_mod"
    assert spec.schema_version is None


def test_module_with_schema_version_v1_still_loads():
    """NT-3: Existing schema_version: 'worldmodule.v1' loads cleanly (backward compat)."""
    spec = WorldModuleSpec.model_validate(_make_minimal({"schema_version": "worldmodule.v1"}))
    assert spec.schema_version == "worldmodule.v1"
    assert spec.module_id == "test_mod"


def test_normalized_world_module_has_no_schema_version_field():
    """Guard 2: dataclasses.fields confirms schema_version is absent from NormalizedWorldModule."""
    field_names = {f.name for f in dataclasses.fields(NormalizedWorldModule)}
    assert "schema_version" not in field_names


def test_worldmodulespec_accepts_any_schema_version_string():
    """Guard 3: Arbitrary schema_version value no longer raises ValidationError."""
    spec = WorldModuleSpec.model_validate(_make_minimal({"schema_version": "worldmodule.future"}))
    assert spec.schema_version == "worldmodule.future"
