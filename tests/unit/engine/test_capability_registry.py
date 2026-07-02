"""Unit tests for the capability registry YAML and Python reader."""
from pathlib import Path

import pytest
import yaml

from src.engine.capability import CapabilityRegistry, VALID_STATUSES

_REGISTRY_PATH = Path("docs/engine/capability_registry.yaml")
_REQUIRED_FIELDS = {"capability_id", "name", "status", "description", "since_version"}


@pytest.fixture(scope="module")
def registry_data():
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def registry():
    return CapabilityRegistry()


def test_capability_registry_yaml_exists():
    assert _REGISTRY_PATH.exists(), f"capability_registry.yaml missing at {_REGISTRY_PATH}"


def test_capability_registry_is_valid_yaml(registry_data):
    assert "capabilities" in registry_data
    assert isinstance(registry_data["capabilities"], list)


def test_all_registry_entries_have_required_fields(registry_data):
    for entry in registry_data["capabilities"]:
        missing = _REQUIRED_FIELDS - entry.keys()
        assert not missing, f"Entry {entry.get('capability_id')} missing fields: {missing}"


def test_all_registry_statuses_are_valid(registry_data):
    for entry in registry_data["capabilities"]:
        status = entry.get("status")
        assert status in VALID_STATUSES, (
            f"Invalid status '{status}' for capability '{entry.get('capability_id')}'"
        )


def test_registry_has_minimum_entries(registry_data):
    count = len(registry_data["capabilities"])
    assert count >= 20, f"Registry has only {count} entries (minimum 20 required)"


def test_capability_reader_is_supported(registry):
    assert registry.is_supported("quest_generation") is True


def test_capability_reader_is_unsupported(registry):
    assert registry.is_supported("complex_pathfinding") is False


def test_capability_reader_get_status(registry):
    assert registry.get_status("deterministic_replay") == "OFFICIAL"


def test_capability_reader_unknown_id(registry):
    assert registry.get_status("nonexistent_capability_xyz") is None
