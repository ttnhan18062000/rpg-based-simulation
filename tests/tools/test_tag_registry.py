"""Tests for tools/tag_registry.py."""

import json
import sys
from pathlib import Path

import pytest

# Ensure tools/ is importable.
_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from tag_registry import (  # noqa: E402
    ADDABLE_CATEGORIES,
    ALL_CATEGORIES,
    add_tag,
    canonical_form_violation,
    check_tags_registered,
    is_phase_milestone_tag,
    is_tag_registered,
    load_registry,
    registry_path,
)

# ---------------------------------------------------------------------------
# canonical_form_violation
# ---------------------------------------------------------------------------


def test_canonical_form_violation_none_for_valid_tag():
    assert canonical_form_violation("faction") is None
    assert canonical_form_violation("some-oneoff-tag") is None


def test_canonical_form_violation_forbidden_priority_tag():
    assert canonical_form_violation("p0") is not None
    assert canonical_form_violation("P0") is not None


def test_canonical_form_violation_uppercase():
    assert canonical_form_violation("Combat") is not None


def test_canonical_form_violation_underscore():
    assert canonical_form_violation("simulation_quality") is not None


def test_canonical_form_violation_noncanonical_phase():
    assert canonical_form_violation("phase5") is not None
    assert canonical_form_violation("phase-5") is None


def test_canonical_form_violation_known_synonym():
    assert canonical_form_violation("sim") is not None
    assert canonical_form_violation("cog") is not None


# ---------------------------------------------------------------------------
# is_phase_milestone_tag / is_tag_registered
# ---------------------------------------------------------------------------


def test_is_phase_milestone_tag():
    assert is_phase_milestone_tag("phase-5")
    assert is_phase_milestone_tag("phase-12")
    assert not is_phase_milestone_tag("phase5")
    assert not is_phase_milestone_tag("faction")


def test_is_tag_registered_true_for_registered_tag():
    registry = {"faction": {"tag": "faction", "category": "subsystem-topic"}}
    assert is_tag_registered("faction", registry)


def test_is_tag_registered_true_for_phase_tag_without_registration():
    assert is_tag_registered("phase-5", {})


def test_is_tag_registered_false_for_unregistered_non_phase_tag():
    assert not is_tag_registered("some-unregistered-tag", {})


# ---------------------------------------------------------------------------
# load_registry
# ---------------------------------------------------------------------------


def test_load_registry_missing_file_returns_empty(tmp_path):
    assert load_registry(tmp_path) == {}


def test_load_registry_reads_entries(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"tag": "faction", "category": "subsystem-topic", "added_date": "2026-07-06", "note": ""}) + "\n"
        + json.dumps({"tag": "debugging", "category": "process-skill-signal", "added_date": "2026-07-06", "note": ""}) + "\n",
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert set(registry) == {"faction", "debugging"}
    assert registry["faction"]["category"] == "subsystem-topic"


def test_load_registry_skips_blank_lines(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n"
        + json.dumps({"tag": "faction", "category": "subsystem-topic", "added_date": "2026-07-06", "note": ""}) + "\n"
        + "\n",
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert set(registry) == {"faction"}


def test_load_registry_raises_on_duplicate_tag(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    entry = json.dumps({"tag": "faction", "category": "subsystem-topic", "added_date": "2026-07-06", "note": ""})
    path.write_text(entry + "\n" + entry + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate registration"):
        load_registry(tmp_path)


# ---------------------------------------------------------------------------
# add_tag
# ---------------------------------------------------------------------------


def test_add_tag_appends_entry_and_returns_it(tmp_path):
    entry = add_tag("faction", "subsystem-topic", note="test note", root=tmp_path)

    assert entry["tag"] == "faction"
    assert entry["category"] == "subsystem-topic"
    assert entry["note"] == "test note"
    assert "added_date" in entry

    registry = load_registry(tmp_path)
    assert "faction" in registry


def test_add_tag_rejects_non_canonical_tag(tmp_path):
    with pytest.raises(ValueError, match="canonical form"):
        add_tag("Combat", "subsystem-topic", root=tmp_path)


def test_add_tag_rejects_invalid_category(tmp_path):
    with pytest.raises(ValueError, match="category must be one of"):
        add_tag("faction", "not-a-real-category", root=tmp_path)


def test_add_tag_rejects_phase_milestone_category(tmp_path):
    """phase-milestone is a recognized category but not addable — phase tags are pattern-matched."""
    assert "phase-milestone" not in ADDABLE_CATEGORIES
    assert "phase-milestone" in ALL_CATEGORIES
    with pytest.raises(ValueError, match="category must be one of"):
        add_tag("some-tag", "phase-milestone", root=tmp_path)


def test_add_tag_rejects_duplicate_tag(tmp_path):
    add_tag("faction", "subsystem-topic", root=tmp_path)

    with pytest.raises(ValueError, match="already registered"):
        add_tag("faction", "quality-attribute", root=tmp_path)


def test_add_tag_is_append_only_existing_entries_unchanged(tmp_path):
    add_tag("faction", "subsystem-topic", note="first", root=tmp_path)
    add_tag("debugging", "process-skill-signal", note="second", root=tmp_path)

    registry = load_registry(tmp_path)

    assert registry["faction"]["note"] == "first"
    assert registry["debugging"]["note"] == "second"
    assert len(registry) == 2


# ---------------------------------------------------------------------------
# check_tags_registered (TCK-20260706-SCOPE-TAG-REGISTRY-CHECK)
# ---------------------------------------------------------------------------


def test_check_tags_registered_all_registered_returns_empty(tmp_path):
    add_tag("faction", "subsystem-topic", root=tmp_path)
    add_tag("debugging", "process-skill-signal", root=tmp_path)

    assert check_tags_registered(["faction", "debugging"], root=tmp_path) == []


def test_check_tags_registered_returns_only_unregistered_subset(tmp_path):
    add_tag("faction", "subsystem-topic", root=tmp_path)

    result = check_tags_registered(["faction", "some-new-tag", "another-new-tag"], root=tmp_path)

    assert result == ["some-new-tag", "another-new-tag"]


def test_check_tags_registered_phase_tags_never_flagged(tmp_path):
    result = check_tags_registered(["phase-5", "some-new-tag"], root=tmp_path)

    assert result == ["some-new-tag"]


def test_check_tags_registered_empty_input_returns_empty(tmp_path):
    assert check_tags_registered([], root=tmp_path) == []
