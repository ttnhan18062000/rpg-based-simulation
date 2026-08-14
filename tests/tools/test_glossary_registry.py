"""Tests for tools/glossary_registry.py (TCK-20260718-GLOSSARY-REGISTRY).

Mirrors tests/tools/test_layer_registry.py's structure — same registry-file-I/O shape — with
category validation (like tag_registry.py) and description-required validation (unique to this
module, since a blank tooltip is a real defect this registry itself should catch) instead of
layer_registry.py's canonical-form checking (deliberately absent here — see
tools/glossary_registry.py's module docstring for why).
"""

import json
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from glossary_registry import (  # noqa: E402
    GLOSSARY_CATEGORIES,
    add_term,
    is_term_registered,
    load_registry,
    registry_path,
)

# ---------------------------------------------------------------------------
# is_term_registered
# ---------------------------------------------------------------------------


def test_is_term_registered_true_for_registered_term():
    registry = {"DONE": {"term": "DONE"}}
    assert is_term_registered("DONE", registry)


def test_is_term_registered_false_for_unregistered_term():
    assert not is_term_registered("NOT_A_REAL_TERM", {})


def test_is_term_registered_case_sensitive():
    # "ok" (event-status) and "OK" are deliberately distinct terms — case-sensitive lookup is a
    # documented design decision (module docstring), not an oversight.
    registry = {"ok": {"term": "ok"}}
    assert is_term_registered("ok", registry)
    assert not is_term_registered("OK", registry)


# ---------------------------------------------------------------------------
# load_registry
# ---------------------------------------------------------------------------


def test_load_registry_missing_file_returns_empty(tmp_path):
    assert load_registry(tmp_path) == {}


def test_load_registry_reads_entries(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"term": "DONE", "category": "ticket-status", "added_date": "2026-07-18", "description": "x"}) + "\n"
        + json.dumps({"term": "OPEN", "category": "ticket-status", "added_date": "2026-07-18", "description": "y"}) + "\n",
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert set(registry) == {"DONE", "OPEN"}


def test_load_registry_skips_blank_lines(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        "\n" + json.dumps({"term": "DONE", "category": "ticket-status", "added_date": "2026-07-18", "description": "x"}) + "\n\n",
        encoding="utf-8",
    )

    registry = load_registry(tmp_path)

    assert set(registry) == {"DONE"}


def test_load_registry_raises_on_duplicate_term(tmp_path):
    path = registry_path(tmp_path)
    path.parent.mkdir(parents=True)
    entry = json.dumps({"term": "DONE", "category": "ticket-status", "added_date": "2026-07-18", "description": "x"})
    path.write_text(entry + "\n" + entry + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate registration"):
        load_registry(tmp_path)


# ---------------------------------------------------------------------------
# add_term
# ---------------------------------------------------------------------------


def test_add_term_appends_entry_and_returns_it(tmp_path):
    entry = add_term("DONE", "ticket-status", "Work is complete.", root=tmp_path)

    assert entry["term"] == "DONE"
    assert entry["category"] == "ticket-status"
    assert entry["description"] == "Work is complete."
    assert "added_date" in entry

    registry = load_registry(tmp_path)
    assert "DONE" in registry


def test_add_term_rejects_invalid_category(tmp_path):
    with pytest.raises(ValueError, match="category must be one of"):
        add_term("DONE", "not-a-real-category", "Work is complete.", root=tmp_path)


def test_add_term_rejects_blank_description(tmp_path):
    with pytest.raises(ValueError, match="description must not be blank"):
        add_term("DONE", "ticket-status", "", root=tmp_path)


def test_add_term_rejects_whitespace_only_description(tmp_path):
    with pytest.raises(ValueError, match="description must not be blank"):
        add_term("DONE", "ticket-status", "   ", root=tmp_path)


def test_add_term_rejects_duplicate_term(tmp_path):
    add_term("DONE", "ticket-status", "Work is complete.", root=tmp_path)

    with pytest.raises(ValueError, match="already registered"):
        add_term("DONE", "ticket-status", "A different description.", root=tmp_path)


def test_add_term_is_append_only_existing_entries_unchanged(tmp_path):
    add_term("DONE", "ticket-status", "first", root=tmp_path)
    add_term("OPEN", "ticket-status", "second", root=tmp_path)

    registry = load_registry(tmp_path)

    assert registry["DONE"]["description"] == "first"
    assert registry["OPEN"]["description"] == "second"
    assert len(registry) == 2


def test_add_term_no_canonical_form_check_mixed_case_and_underscores_allowed(tmp_path):
    # Deliberately different from tag_registry.py/layer_registry.py: glossary terms are existing
    # fixed strings this repo's own code emits verbatim, not freely-chosen labels — mixed case
    # (DONE, P0) and underscores (dod_condition_failed) are both legitimate, real terms.
    add_term("dod_condition_failed", "reason-code", "x", root=tmp_path)
    add_term("P0", "priority", "y", root=tmp_path)

    registry = load_registry(tmp_path)
    assert "dod_condition_failed" in registry
    assert "P0" in registry


# ---------------------------------------------------------------------------
# GLOSSARY_CATEGORIES / real seeded registry
# ---------------------------------------------------------------------------


def test_glossary_categories_is_the_expected_fixed_set():
    assert GLOSSARY_CATEGORIES == {
        "ticket-status",
        "run-status",
        "reason-code",
        "event-status",
        "tier",
        "priority",
        "type",
        "phase",
    }


def test_add_term_accepts_phase_category(tmp_path):
    entry = add_term("Scope", "phase", "Creates the ticket file.", root=tmp_path)

    assert entry["category"] == "phase"
    registry = load_registry(tmp_path)
    assert registry["Scope"]["category"] == "phase"


def test_real_seeded_registry_covers_every_canonical_ticket_field_value():
    # Against the real, seeded repo registry (no root override) — proves the live seeding actually
    # covered tools/ticket_field_values.py's own canonical enums, not just that the mechanism
    # works on a fixture.
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))
    from ticket_field_values import PRIORITY_VALUES, TIER_VALUES, WORKFLOW_STATUS_VALUES

    registry = load_registry()

    for value in TIER_VALUES | PRIORITY_VALUES | WORKFLOW_STATUS_VALUES:
        assert value in registry, f"{value!r} has no glossary entry"


def test_real_seeded_registry_covers_every_workflow_phase():
    # Against the real, seeded repo registry (no root override) — proves the live seeding actually
    # covered every distinct literal in tools/agent-monitoring/vocabulary.py's WORKFLOW_PHASES,
    # imported directly rather than re-derived, so a casing/spacing typo at registration time
    # would fail this test instead of silently registering a dead term (see plan.md's Anti-Drift
    # Notes for why byte-exact casing is load-bearing here).
    agent_monitoring_dir = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
    if str(agent_monitoring_dir) not in sys.path:
        sys.path.insert(0, str(agent_monitoring_dir))
    from vocabulary import WORKFLOW_PHASES

    all_phases: set[str] = set()
    for phases in WORKFLOW_PHASES.values():
        all_phases |= phases

    registry = load_registry()

    for phase in all_phases:
        assert phase in registry, f"{phase!r} has no glossary entry"
        assert registry[phase]["category"] == "phase", f"{phase!r} is registered under the wrong category"
        assert registry[phase]["description"].strip(), f"{phase!r} has a blank description"


def test_real_seeded_registry_every_entry_has_non_blank_description():
    registry = load_registry()
    for term, entry in registry.items():
        assert entry.get("description", "").strip(), f"{term!r} has a blank description"


def test_real_seeded_registry_every_entry_has_valid_category():
    registry = load_registry()
    for term, entry in registry.items():
        assert entry["category"] in GLOSSARY_CATEGORIES, f"{term!r} has invalid category {entry['category']!r}"
