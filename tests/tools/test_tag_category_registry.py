"""Tests for tools/tag_registry.py's category-registry surface (TCK-20260720-TAG-CATEGORY-REGISTRY).

Mirrors tests/tools/test_layer_registry.py's structure — category_registry_path/
load_category_registry/is_category_registered/add_category/category_values are a second,
independent registry surface living inside tag_registry.py (not a sibling module), keyed on
"category" instead of "layer".
"""

import json
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from tag_registry import (  # noqa: E402
    add_category,
    canonical_form_violation,
    category_registry_path,
    category_values,
    is_category_registered,
    load_category_registry,
    main,
)

# ---------------------------------------------------------------------------
# canonical_form_violation (reused module-level function — sanity check only)
# ---------------------------------------------------------------------------


def test_canonical_form_violation_none_for_valid_category():
    assert canonical_form_violation("subsystem-topic") is None
    assert canonical_form_violation("some-new-category") is None


def test_canonical_form_violation_uppercase():
    assert canonical_form_violation("Subsystem-Topic") is not None


def test_canonical_form_violation_underscore():
    assert canonical_form_violation("subsystem_topic") is not None


# ---------------------------------------------------------------------------
# is_category_registered
# ---------------------------------------------------------------------------


def test_is_category_registered_true_for_registered_category():
    registry = {"subsystem-topic": {"category": "subsystem-topic"}}
    assert is_category_registered("subsystem-topic", registry)


def test_is_category_registered_false_for_unregistered_category():
    assert not is_category_registered("some-unregistered-category", {})


# ---------------------------------------------------------------------------
# load_category_registry
# ---------------------------------------------------------------------------


def test_load_category_registry_missing_file_returns_empty(tmp_path):
    assert load_category_registry(tmp_path) == {}


def test_load_category_registry_reads_entries(tmp_path):
    path = category_registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"category": "subsystem-topic", "added_date": "2026-07-20", "note": ""}) + "\n"
        + json.dumps({"category": "meta-process", "added_date": "2026-07-20", "note": ""}) + "\n",
        encoding="utf-8",
    )

    registry = load_category_registry(tmp_path)

    assert set(registry) == {"subsystem-topic", "meta-process"}


def test_load_category_registry_skips_blank_lines(tmp_path):
    path = category_registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n"
        + json.dumps({"category": "subsystem-topic", "added_date": "2026-07-20", "note": ""})
        + "\n\n",
        encoding="utf-8",
    )

    registry = load_category_registry(tmp_path)

    assert set(registry) == {"subsystem-topic"}


def test_load_category_registry_raises_on_duplicate_category(tmp_path):
    path = category_registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    entry = json.dumps({"category": "subsystem-topic", "added_date": "2026-07-20", "note": ""})
    path.write_text(entry + "\n" + entry + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate registration"):
        load_category_registry(tmp_path)


# ---------------------------------------------------------------------------
# add_category
# ---------------------------------------------------------------------------


def test_add_category_appends_entry_and_returns_it(tmp_path):
    entry = add_category("subsystem-topic", note="test note", root=tmp_path)

    assert set(entry) == {"category", "added_date", "note"}
    assert entry["category"] == "subsystem-topic"
    assert entry["note"] == "test note"
    assert "added_date" in entry

    registry = load_category_registry(tmp_path)
    assert "subsystem-topic" in registry


def test_add_category_rejects_non_canonical_category(tmp_path):
    with pytest.raises(ValueError, match="canonical form"):
        add_category("Subsystem-Topic", root=tmp_path)


def test_add_category_rejects_duplicate_category(tmp_path):
    add_category("subsystem-topic", root=tmp_path)

    with pytest.raises(ValueError, match="already registered"):
        add_category("subsystem-topic", root=tmp_path)


def test_add_category_is_append_only_existing_entries_unchanged(tmp_path):
    add_category("subsystem-topic", note="first", root=tmp_path)
    add_category("meta-process", note="second", root=tmp_path)

    registry = load_category_registry(tmp_path)

    assert registry["subsystem-topic"]["note"] == "first"
    assert registry["meta-process"]["note"] == "second"
    assert len(registry) == 2


# ---------------------------------------------------------------------------
# add-category CLI subcommand
# ---------------------------------------------------------------------------


def test_add_category_cli_registers_category(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        ["tag_registry.py", "add-category", "some-new-cat", "--note", "test", "--root", str(tmp_path)],
    )

    main()

    assert "some-new-cat" in load_category_registry(tmp_path)


# ---------------------------------------------------------------------------
# category_values
# ---------------------------------------------------------------------------


def test_category_values_returns_frozenset_of_registered_categories(tmp_path):
    add_category("subsystem-topic", root=tmp_path)
    add_category("meta-process", root=tmp_path)

    result = category_values(tmp_path)

    assert result == frozenset({"subsystem-topic", "meta-process"})
    assert isinstance(result, frozenset)


def test_category_values_matches_real_seeded_registry():
    # Against the real, seeded repo registry (no root override) — proves the live conversion
    # actually seeded exactly the 4 addable categories, not just that the mechanism works on a
    # fixture. phase-milestone is deliberately excluded (never seeded, stays code-side).
    assert category_values() == frozenset(
        {"subsystem-topic", "process-skill-signal", "quality-attribute", "meta-process"}
    )
    assert "phase-milestone" not in category_values()
