"""Tests for tools/mechanism_registry/mechanism_status_language_check.py.

TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION. Prose describes what a mechanism does; it never
states whether it currently works -- that's the registry's job. This detector surfaces status
vocabulary embedded in the atlas/capabilities `desc` fields and the wiring map's own Entity
Operating Loop node labels, report-only, never blocking.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.mechanism_registry.mechanism_status_language_check import (
    scan_atlas,
    scan_capabilities,
    scan_wiring_map_labels,
    STATUS_PHRASES,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_ATLAS_PATH = REPO_ROOT / "docs" / "brainstorm" / "rpg_feature_atlas.html"
_CAPABILITIES_PATH = REPO_ROOT / "docs" / "brainstorm" / "simulation_capabilities.html"
_WIRING_MAP_PATH = REPO_ROOT / "docs" / "brainstorm" / "rpg_simulation_wiring_map.html"


# ---------------------------------------------------------------------------
# scan_atlas
# ---------------------------------------------------------------------------


def test_scan_atlas_finds_status_phrase_in_desc():
    html = (
        '<script type="application/json" id="card-sections-data">\n'
        '{"combat": [{"title": "Foo", "desc": "This mechanism is confirmed live and works well."}]}\n'
        "</script>"
    )
    hits = scan_atlas(html)
    assert len(hits) == 1
    assert hits[0].phrase == "confirmed live"
    assert hits[0].artifact == "atlas"
    assert "combat#0" in hits[0].location


def test_scan_atlas_ignores_badges_and_title():
    """The badges field IS the registry's own intentional, already-checked status surface
    (mechanism_atlas_regenerate.py keeps it converged with mechanisms.yaml directly) -- scanning
    it here would be redundant, not additive, and title text is a citation, not prose."""
    html = (
        '<script type="application/json" id="card-sections-data">\n'
        '{"combat": [{"title": "Confirmed Live Mechanism", "badges": [{"cls": "done", "text": "currently done"}], "desc": "A mechanism that resolves damage."}]}\n'
        "</script>"
    )
    hits = scan_atlas(html)
    assert hits == []


def test_scan_atlas_no_json_block_returns_empty():
    assert scan_atlas("<html>no script block here</html>") == []


# ---------------------------------------------------------------------------
# scan_capabilities
# ---------------------------------------------------------------------------


def test_scan_capabilities_finds_status_phrase_in_desc_not_tierlabel():
    html = (
        '<script type="application/json" id="sections-data">\n'
        '[{"id": "action", "cards": [{"title": "Foo", "tier": "live", "tierLabel": "Live in the simulation", "desc": "This currently does nothing useful."}]}]\n'
        "</script>"
    )
    hits = scan_capabilities(html)
    assert len(hits) == 1
    assert hits[0].phrase == "currently"
    assert hits[0].artifact == "capabilities"


# ---------------------------------------------------------------------------
# scan_wiring_map_labels
# ---------------------------------------------------------------------------


def test_scan_wiring_map_labels_finds_status_phrase():
    html = 'FOO["Foo Mechanism<br/>does a thing — confirmed live via bar.py"]'
    hits = scan_wiring_map_labels(html)
    assert len(hits) == 1
    assert hits[0].phrase == "confirmed live"
    assert hits[0].location == "node FOO"


def test_scan_wiring_map_labels_clean_label_no_hits():
    html = 'FOO["Foo Mechanism<br/>does a thing"]'
    assert scan_wiring_map_labels(html) == []


# ---------------------------------------------------------------------------
# report-only guarantee
# ---------------------------------------------------------------------------


def test_main_always_exits_zero_even_with_hits():
    """AC #2: this detector must never fail the build, regardless of hit count."""
    result = subprocess.run(
        [sys.executable, "tools/mechanism_registry/mechanism_status_language_check.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0


def test_make_target_runs_clean():
    result = subprocess.run(
        ["make", "mechanism-status-language-check"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# real corpus
# ---------------------------------------------------------------------------


def test_wiring_map_entity_operating_loop_labels_are_clean():
    """Scope item 3, performed: the wiring map's own node labels should carry zero status
    vocabulary since classDef colouring already derives from the registry -- a second, unchecked
    place for the same fact to live and drift."""
    html = _WIRING_MAP_PATH.read_text(encoding="utf-8")
    hits = scan_wiring_map_labels(html)
    assert hits == [], f"wiring map node labels still carry status language: {hits}"


def test_real_corpus_scan_runs_without_error():
    """Not a zero-hits assertion -- the atlas/capabilities' own extensive, deliberate "currently
    X" phrasing is real, accurate-at-verification status information (see this ticket's own
    Completion Summary for the documented policy), not stale duplication to bulk-strip. This test
    only proves the scan itself runs cleanly against the real, committed files."""
    scan_atlas(_ATLAS_PATH.read_text(encoding="utf-8"))
    scan_capabilities(_CAPABILITIES_PATH.read_text(encoding="utf-8"))
    scan_wiring_map_labels(_WIRING_MAP_PATH.read_text(encoding="utf-8"))


def test_status_phrases_list_is_nonempty():
    assert len(STATUS_PHRASES) > 0
