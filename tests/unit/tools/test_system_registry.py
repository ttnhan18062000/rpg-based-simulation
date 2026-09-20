"""Tests for tools/mechanism_registry/system_registry.py
(TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION).

Mirrors tests/tools/test_layer_registry.py's structure exactly -- `system_registry.py` is a
direct structural copy of `layer_registry.py`, adapted for the mechanism-`systems` domain (see
that module's own docstring for the two deliberate differences: it does not itself hold
membership, and it IS checked for orphans by registry.py::validate() -- neither difference
changes this file's own add/list/canonical-form behavior, which is what's tested here).
"""
from __future__ import annotations

import json

import pytest

from tools.mechanism_registry.system_registry import (
    add_system,
    canonical_form_violation,
    check_systems_registered,
    is_system_registered,
    load_registry,
    registry_path,
    system_values,
)

# ---------------------------------------------------------------------------
# canonical_form_violation
# ---------------------------------------------------------------------------


def test_canonical_form_violation_none_for_valid_system():
    assert canonical_form_violation("combat") is None
    assert canonical_form_violation("some_new_system") is None


def test_canonical_form_violation_uppercase():
    assert canonical_form_violation("Combat") is not None


def test_canonical_form_violation_hyphen():
    assert canonical_form_violation("some-system") is not None


# ---------------------------------------------------------------------------
# is_system_registered
# ---------------------------------------------------------------------------


def test_is_system_registered_true_for_registered_system():
    registry = {"combat": {"system": "combat"}}
    assert is_system_registered("combat", registry)


def test_is_system_registered_false_for_unregistered_system():
    assert not is_system_registered("some_unregistered_system", {})


# ---------------------------------------------------------------------------
# load_registry
# ---------------------------------------------------------------------------


def test_load_registry_missing_file_returns_empty(tmp_path):
    assert load_registry(tmp_path) == {}


def test_load_registry_reads_entries(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"system": "combat", "added_date": "2026-09-19", "note": ""}) + "\n"
        + json.dumps({"system": "economy", "added_date": "2026-09-19", "note": ""}) + "\n",
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert set(registry) == {"combat", "economy"}


def test_load_registry_skips_blank_lines(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n" + json.dumps({"system": "combat", "added_date": "2026-09-19", "note": ""}) + "\n\n",
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert set(registry) == {"combat"}


def test_load_registry_raises_on_duplicate_system(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    entry = json.dumps({"system": "combat", "added_date": "2026-09-19", "note": ""})
    path.write_text(entry + "\n" + entry + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate registration"):
        load_registry(tmp_path)


# ---------------------------------------------------------------------------
# add_system
# ---------------------------------------------------------------------------


def test_add_system_appends_entry_and_returns_it(tmp_path):
    entry = add_system("combat", note="test note", root=tmp_path)

    assert entry["system"] == "combat"
    assert entry["note"] == "test note"
    assert "added_date" in entry

    registry = load_registry(tmp_path)
    assert "combat" in registry


def test_add_system_rejects_non_canonical_system(tmp_path):
    with pytest.raises(ValueError, match="canonical form"):
        add_system("Combat", root=tmp_path)


def test_add_system_rejects_duplicate_system(tmp_path):
    add_system("combat", root=tmp_path)

    with pytest.raises(ValueError, match="already registered"):
        add_system("combat", root=tmp_path)


def test_add_system_is_append_only_existing_entries_unchanged(tmp_path):
    add_system("combat", note="first", root=tmp_path)
    add_system("economy", note="second", root=tmp_path)

    registry = load_registry(tmp_path)

    assert registry["combat"]["note"] == "first"
    assert registry["economy"]["note"] == "second"
    assert len(registry) == 2


# ---------------------------------------------------------------------------
# check_systems_registered
# ---------------------------------------------------------------------------


def test_check_systems_registered_all_registered_returns_empty(tmp_path):
    add_system("combat", root=tmp_path)
    add_system("economy", root=tmp_path)

    assert check_systems_registered(["combat", "economy"], root=tmp_path) == []


def test_check_systems_registered_returns_only_unregistered_subset(tmp_path):
    add_system("combat", root=tmp_path)

    result = check_systems_registered(["combat", "some_new_system"], root=tmp_path)

    assert result == ["some_new_system"]


def test_check_systems_registered_empty_input_returns_empty(tmp_path):
    assert check_systems_registered([], root=tmp_path) == []


# ---------------------------------------------------------------------------
# system_values
# ---------------------------------------------------------------------------


def test_system_values_returns_frozenset_of_registered_systems(tmp_path):
    add_system("combat", root=tmp_path)
    add_system("economy", root=tmp_path)

    result = system_values(tmp_path)

    assert result == frozenset({"combat", "economy"})
    assert isinstance(result, frozenset)


def test_system_values_matches_real_seeded_registry():
    # Against the real, seeded repo registry (no root override) -- proves the 7-system
    # vocabulary from TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION was actually
    # registered, not just that the mechanism works on a fixture.
    expected = {"combat", "progression", "cognition", "social", "faction", "economy", "world"}
    assert system_values() == expected
