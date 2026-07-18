"""Tests for tools/layer_registry.py (TCK-20260718-LAYER-REGISTRY-CONVERSION).

Mirrors tests/tools/test_tag_registry.py's structure, minus the category dimension (Layer has
none — see tools/layer_registry.py's module docstring for why).
"""

import json
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from layer_registry import (  # noqa: E402
    add_layer,
    canonical_form_violation,
    check_layers_registered,
    is_layer_registered,
    layer_values,
    load_registry,
    registry_path,
)

# ---------------------------------------------------------------------------
# canonical_form_violation
# ---------------------------------------------------------------------------


def test_canonical_form_violation_none_for_valid_layer():
    assert canonical_form_violation("economy") is None
    assert canonical_form_violation("some-new-layer") is None


def test_canonical_form_violation_uppercase():
    assert canonical_form_violation("Economy") is not None


def test_canonical_form_violation_underscore():
    assert canonical_form_violation("some_layer") is not None


# ---------------------------------------------------------------------------
# is_layer_registered
# ---------------------------------------------------------------------------


def test_is_layer_registered_true_for_registered_layer():
    registry = {"economy": {"layer": "economy"}}
    assert is_layer_registered("economy", registry)


def test_is_layer_registered_false_for_unregistered_layer():
    assert not is_layer_registered("some-unregistered-layer", {})


# ---------------------------------------------------------------------------
# load_registry
# ---------------------------------------------------------------------------


def test_load_registry_missing_file_returns_empty(tmp_path):
    assert load_registry(tmp_path) == {}


def test_load_registry_reads_entries(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"layer": "economy", "added_date": "2026-07-18", "note": ""}) + "\n"
        + json.dumps({"layer": "combat", "added_date": "2026-07-18", "note": ""}) + "\n",
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert set(registry) == {"economy", "combat"}


def test_load_registry_skips_blank_lines(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n" + json.dumps({"layer": "economy", "added_date": "2026-07-18", "note": ""}) + "\n\n",
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert set(registry) == {"economy"}


def test_load_registry_raises_on_duplicate_layer(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    entry = json.dumps({"layer": "economy", "added_date": "2026-07-18", "note": ""})
    path.write_text(entry + "\n" + entry + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate registration"):
        load_registry(tmp_path)


# ---------------------------------------------------------------------------
# add_layer
# ---------------------------------------------------------------------------


def test_add_layer_appends_entry_and_returns_it(tmp_path):
    entry = add_layer("economy", note="test note", root=tmp_path)

    assert entry["layer"] == "economy"
    assert entry["note"] == "test note"
    assert "added_date" in entry
    assert "category" not in entry

    registry = load_registry(tmp_path)
    assert "economy" in registry


def test_add_layer_rejects_non_canonical_layer(tmp_path):
    with pytest.raises(ValueError, match="canonical form"):
        add_layer("Economy", root=tmp_path)


def test_add_layer_rejects_duplicate_layer(tmp_path):
    add_layer("economy", root=tmp_path)

    with pytest.raises(ValueError, match="already registered"):
        add_layer("economy", root=tmp_path)


def test_add_layer_is_append_only_existing_entries_unchanged(tmp_path):
    add_layer("economy", note="first", root=tmp_path)
    add_layer("combat", note="second", root=tmp_path)

    registry = load_registry(tmp_path)

    assert registry["economy"]["note"] == "first"
    assert registry["combat"]["note"] == "second"
    assert len(registry) == 2


# ---------------------------------------------------------------------------
# check_layers_registered
# ---------------------------------------------------------------------------


def test_check_layers_registered_all_registered_returns_empty(tmp_path):
    add_layer("economy", root=tmp_path)
    add_layer("combat", root=tmp_path)

    assert check_layers_registered(["economy", "combat"], root=tmp_path) == []


def test_check_layers_registered_returns_only_unregistered_subset(tmp_path):
    add_layer("economy", root=tmp_path)

    result = check_layers_registered(["economy", "some-new-layer"], root=tmp_path)

    assert result == ["some-new-layer"]


def test_check_layers_registered_empty_input_returns_empty(tmp_path):
    assert check_layers_registered([], root=tmp_path) == []


# ---------------------------------------------------------------------------
# layer_values
# ---------------------------------------------------------------------------


def test_layer_values_returns_frozenset_of_registered_layers(tmp_path):
    add_layer("economy", root=tmp_path)
    add_layer("combat", root=tmp_path)

    result = layer_values(tmp_path)

    assert result == frozenset({"economy", "combat"})
    assert isinstance(result, frozenset)


def test_layer_values_matches_real_seeded_registry():
    # Against the real, seeded repo registry (no root override) — proves the live conversion
    # actually seeded all 19 original LAYER_VALUES, not just that the mechanism works on a fixture.
    expected = {
        "mechanics", "engine", "testing", "simulation", "ai", "architecture",
        "core", "ticket", "artifact", "guidelines", "observability", "performance",
        "combat", "compliance", "strategy", "systems", "economy", "world", "misc",
    }
    assert layer_values() == expected
