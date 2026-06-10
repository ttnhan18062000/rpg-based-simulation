"""
Schema validation tests for data/content/compatibility/migration_map.yaml.

Verifies that every entry contains all required fields and uses only
valid status and family values. Rejects entries with missing required fields.
"""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.catalog

MIGRATION_MAP_PATH = Path("data/content/compatibility/migration_map.yaml")

REQUIRED_FIELDS = frozenset({
    "legacy_id",
    "legacy_family",
    "catalog_family",
    "catalog_id",
    "adapter",
    "status",
    "fallback_allowed",
})

VALID_STATUSES = frozenset({
    "catalog_authoritative",
    "compat_projected",
    "fallback_only",
    "quarantined",
    "deprecated",
    "removed",
})

VALID_LEGACY_FAMILIES = frozenset({
    "resource",
    "recipe",
    "region",
    "enemy",
    "role_enum",
    "faction_enum",
    "item",
    "service",
})


@pytest.fixture(scope="module")
def migration_map():
    assert MIGRATION_MAP_PATH.is_file(), f"migration_map.yaml not found at {MIGRATION_MAP_PATH}"
    with open(MIGRATION_MAP_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def entries(migration_map):
    assert "entries" in migration_map, "migration_map.yaml must have an 'entries' key"
    assert isinstance(migration_map["entries"], list)
    return migration_map["entries"]


def test_migration_map_file_exists():
    assert MIGRATION_MAP_PATH.is_file()


def test_migration_map_has_schema_version(migration_map):
    assert migration_map.get("schema_version") == "migration_map.v1"


def test_migration_map_has_entries(entries):
    assert len(entries) > 0, "migration_map.yaml must have at least one entry"


def test_all_entries_have_required_fields(entries):
    violations = []
    for i, entry in enumerate(entries):
        missing = REQUIRED_FIELDS - set(entry.keys())
        if missing:
            violations.append(
                f"  Entry[{i}] legacy_id={entry.get('legacy_id', '?')!r}: "
                f"missing fields: {sorted(missing)}"
            )
    assert not violations, (
        f"{len(violations)} entry/entries missing required fields:\n"
        + "\n".join(violations)
    )


def test_all_status_values_are_valid(entries):
    violations = []
    for entry in entries:
        status = entry.get("status", "")
        if status not in VALID_STATUSES:
            violations.append(
                f"  {entry.get('legacy_id', '?')!r}: invalid status {status!r} "
                f"(allowed: {sorted(VALID_STATUSES)})"
            )
    assert not violations, (
        f"{len(violations)} entry/entries have invalid status:\n" + "\n".join(violations)
    )


def test_all_legacy_families_are_known(entries):
    violations = []
    for entry in entries:
        family = entry.get("legacy_family", "")
        if family not in VALID_LEGACY_FAMILIES:
            violations.append(
                f"  {entry.get('legacy_id', '?')!r}: unknown legacy_family {family!r}"
            )
    assert not violations, (
        f"{len(violations)} entry/entries have unknown legacy_family:\n" + "\n".join(violations)
    )


def test_fallback_allowed_is_boolean(entries):
    violations = []
    for entry in entries:
        val = entry.get("fallback_allowed")
        if not isinstance(val, bool):
            violations.append(
                f"  {entry.get('legacy_id', '?')!r}: fallback_allowed must be bool, got {type(val).__name__}"
            )
    assert not violations, "\n".join(violations)


def test_legacy_ids_are_unique(entries):
    seen = {}
    duplicates = []
    for entry in entries:
        key = (entry.get("legacy_id"), entry.get("legacy_family"))
        if key in seen:
            duplicates.append(f"  {key}: appears at indices {seen[key]} and current")
        else:
            seen[key] = entries.index(entry)
    assert not duplicates, f"Duplicate (legacy_id, legacy_family) pairs:\n" + "\n".join(duplicates)


def test_all_required_legacy_families_are_represented(entries):
    """At least one entry per required family must be present."""
    families_present = {e.get("legacy_family") for e in entries}
    required = {"resource", "recipe", "region", "enemy", "role_enum", "faction_enum", "item", "service"}
    missing = required - families_present
    assert not missing, (
        f"Required legacy families missing from migration_map.yaml: {sorted(missing)}"
    )


def test_deprecated_entries_have_notes(entries):
    """Deprecated entries must include a notes field explaining why."""
    violations = []
    for entry in entries:
        if entry.get("status") == "deprecated" and not entry.get("notes"):
            violations.append(f"  {entry.get('legacy_id', '?')!r}: deprecated entry has no notes")
    assert not violations, "\n".join(violations)
