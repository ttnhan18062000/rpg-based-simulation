"""Tests for tools/mechanism_registry.py::all_mechanisms_combined_view and
tools/generate_mechanism_registry_view.py.

TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW. A third generated view (every mechanism, priority +
verification together) alongside the existing verification-only and priority-unverified-only
views -- neither replaces the other two.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.mechanism_registry import all_mechanisms_combined_view
from tools.generate_mechanism_registry_view import render

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_OUTPUT_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanism_registry_view.md"


@pytest.fixture(scope="module")
def registry_data():
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_combined_view_includes_all_mechanisms_not_just_unverified(registry_data):
    """The load-bearing difference from unverified_priority_ranking(): a verified mechanism must
    still appear, with its real priority number, not be dropped."""
    rows = all_mechanisms_combined_view(registry_data)
    ids = {r["id"] for r in rows}
    assert len(rows) == len(registry_data["mechanisms"])
    # action_pacing_readiness is verified (scenario/observed) -- must still be present with a
    # real priority, not silently excluded the way the unverified-only ranking excludes it.
    assert "action_pacing_readiness" in ids
    apr_row = next(r for r in rows if r["id"] == "action_pacing_readiness")
    assert apr_row["priority"] > 0
    assert apr_row["evidence"] == "runtime"


def test_combined_view_sorted_by_priority_descending(registry_data):
    rows = all_mechanisms_combined_view(registry_data)
    priorities = [r["priority"] for r in rows]
    assert priorities == sorted(priorities, reverse=True)


def test_combined_view_evidence_classification_matches_verification_view(registry_data):
    """evidence must agree with the same runtime/static/unverified split
    mechanism_verification_view.md's own generator uses -- not a second, independently-derived
    classification that could silently disagree."""
    from tools.mechanism_registry import RUNTIME_INSTRUMENTS, STATIC_INSTRUMENTS

    rows = all_mechanisms_combined_view(registry_data)
    for r in rows:
        if r["evidence"] == "runtime":
            assert r["instrument"] in RUNTIME_INSTRUMENTS
        elif r["evidence"] == "static":
            assert r["instrument"] in STATIC_INSTRUMENTS
        else:
            assert r["evidence"] == "unverified"
            assert r["instrument"] is None


def test_render_reports_verification_counts_at_the_head(registry_data):
    content = render(registry_data)
    total = len(registry_data["mechanisms"])
    assert f"of {total} total" in content


def test_render_is_not_truncated(registry_data):
    """Completeness is this view's whole purpose -- deliberately not capped at 25 the way the
    priority-only view is."""
    content = render(registry_data)
    total = len(registry_data["mechanisms"])
    row_lines = [
        line for line in content.splitlines()
        if line.startswith("| `") and line.count("|") >= 6
    ]
    assert len(row_lines) == total


def test_make_target_generates_registry_view():
    result = subprocess.run(
        ["make", "mechanism-registry-view"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert _OUTPUT_PATH.exists()


def test_generator_check_mode_detects_staleness(tmp_path):
    stale_output = tmp_path / "mechanism_registry_view.md"
    stale_output.write_text("stale content that will never match", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "tools/generate_mechanism_registry_view.py", "--check",
         "--output", str(stale_output)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "STALE" in result.stdout


def test_real_registry_view_is_up_to_date():
    """The load-bearing regression check: the committed file must match a fresh render, not just
    have been correct at generation time."""
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    expected = render(data)
    actual = _OUTPUT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/brainstorm/mechanism_registry_view.md is stale -- "
        "run `make mechanism-registry-view`"
    )
