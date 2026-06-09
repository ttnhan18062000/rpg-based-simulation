"""
Unit tests for ContentPackManifest schema and ContentPackManifestValidator.
"""

import pytest
from pydantic import ValidationError

from src.content.pack_manifest import (
    MANIFEST_SCHEMA_VERSION,
    ContentPackManifest,
    ContentPackManifestValidator,
    ContentPackValidationError,
)

pytestmark = pytest.mark.catalog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid(**overrides) -> ContentPackManifest:
    defaults = dict(
        schema_version=MANIFEST_SCHEMA_VERSION,
        pack_id="test_pack",
        display_name="Test Pack",
        version="1.0.0",
        sample_compositions=["frontier_only"],
    )
    defaults.update(overrides)
    return ContentPackManifest(**defaults)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

def test_valid_manifest_with_composition():
    m = _valid()
    assert m.pack_id == "test_pack"
    assert m.enabled is True
    assert m.sample_compositions == ["frontier_only"]


def test_valid_manifest_with_scenario_only():
    m = _valid(sample_compositions=[], sample_scenarios=["hero_start"])
    assert m.sample_scenarios == ["hero_start"]


def test_manifest_with_no_consumers_raises():
    with pytest.raises(ValidationError) as exc_info:
        _valid(sample_compositions=[], sample_scenarios=[])
    assert "no consuming" in str(exc_info.value)


def test_manifest_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        _valid(unknown_extra_field="oops")


def test_manifest_is_frozen():
    from pydantic import ValidationError as PydanticValidationError
    m = _valid()
    with pytest.raises((AttributeError, TypeError, PydanticValidationError)):
        m.enabled = False  # type: ignore[misc]


def test_manifest_enabled_flag_defaults_true():
    m = _valid()
    assert m.enabled is True


def test_manifest_disabled_is_valid():
    m = _valid(enabled=False)
    assert m.enabled is False


def test_manifest_pack_id_rejects_uppercase():
    with pytest.raises(ValidationError):
        _valid(pack_id="MyPack")


def test_manifest_pack_id_rejects_leading_digit():
    with pytest.raises(ValidationError):
        _valid(pack_id="1pack")


def test_manifest_dependencies_default_empty():
    m = _valid()
    assert m.dependencies == []


def test_manifest_included_families_default_empty():
    m = _valid()
    assert m.included_families == {}


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------

def test_validator_passes_with_known_dependency():
    m = _valid(dependencies=["base_pack"])
    validator = ContentPackManifestValidator()
    errors = validator.validate(m, known_packs={"base_pack"})
    assert errors == []


def test_validator_fails_missing_dependency():
    m = _valid(dependencies=["missing_pack"])
    validator = ContentPackManifestValidator()
    errors = validator.validate(m, known_packs=set())
    assert len(errors) == 1
    assert "missing_pack" in errors[0]


def test_validator_fails_multiple_missing_dependencies():
    m = _valid(dependencies=["pack_a", "pack_b"])
    validator = ContentPackManifestValidator()
    errors = validator.validate(m, known_packs={"pack_a"})
    assert any("pack_b" in e for e in errors)


def test_validate_or_raise_raises_on_error():
    m = _valid(dependencies=["unknown"])
    validator = ContentPackManifestValidator()
    with pytest.raises(ContentPackValidationError) as exc_info:
        validator.validate_or_raise(m, known_packs=set())
    assert exc_info.value.pack_id == "test_pack"


def test_validate_or_raise_passes_cleanly():
    m = _valid(dependencies=["base"])
    validator = ContentPackManifestValidator()
    validator.validate_or_raise(m, known_packs={"base"})


def test_validator_no_known_packs_defaults_to_empty():
    m = _valid(dependencies=["dep"])
    validator = ContentPackManifestValidator()
    errors = validator.validate(m)
    assert any("dep" in e for e in errors)
