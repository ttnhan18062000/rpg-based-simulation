"""Tests for tools/semantic_control_plane/generate_territory_control_view.py.

TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE. Mirrors
tests/unit/tools/test_mechanism_registry_view.py's own structure. AC 5/AC 6: the Territory view
must render an explicit state for all six architecture.md §8 axes (UNKNOWN is a legitimate,
complete answer, never a blank cell) and show mapped/unmapped + verified/unverified counts
alongside the classification breakdown, never collapsed into one score.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

from tools.mechanism_registry.registry import MechanismRegistry
from tools.semantic_control_plane.generate_territory_control_view import render

REPO_ROOT = Path(__file__).resolve().parents[3]
_RULE_MECHANISM_EDGES_PATH = REPO_ROOT / "registries" / "rule_mechanism_edges.yaml"
_CLASSIFICATIONS_PATH = REPO_ROOT / "registries" / "rule_classifications.yaml"
_OUTPUT_PATH = REPO_ROOT / "docs" / "brainstorm" / "territory_control_management_view.md"

_SIX_AXES = [
    "DESIGN", "REALIZATION", "IMPLEMENTATION", "VERIFICATION", "INTEGRATION", "OBSERVED OUTCOME",
]


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _real_content() -> str:
    rule_mechanism_data = _load_yaml(_RULE_MECHANISM_EDGES_PATH)
    classifications_data = _load_yaml(_CLASSIFICATIONS_PATH)
    return render(rule_mechanism_data, classifications_data, MechanismRegistry())


def test_territory_view_renders_all_six_axes():
    content = _real_content()
    for axis in _SIX_AXES:
        assert axis in content, f"missing axis header {axis!r}"

    # Positive control: the OBSERVED OUTCOME column literally renders UNKNOWN with a stated
    # reason for at least one real Rule row, not a blank cell -- per AC 5's own example text
    # ("OBSERVED OUTCOME: UNKNOWN -- no runtime evidence currently exists").
    assert "UNKNOWN -- no runtime evidence currently exists" in content

    for rule_id in ("TERR-01", "TERR-02", "TERR-03", "TERR-05"):
        assert f"`{rule_id}`" in content
    # TERR-04 is legitimately named in the view's own mapped/unmapped explanatory prose (it is
    # excluded, not silently absent) -- but never as its own `TERR-04` table row.
    assert "`TERR-04`" not in content


def test_territory_view_check_flag_detects_staleness(tmp_path):
    stale_output = tmp_path / "territory_control_management_view.md"
    stale_output.write_text("stale content that will never match", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "tools/semantic_control_plane/generate_territory_control_view.py",
            "--check",
            "--output", str(stale_output),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "STALE" in result.stdout


def test_territory_view_shows_mapped_unmapped_counts():
    content = _real_content()
    assert re.search(r"Mapped / unmapped\*\*: \d+/\d+", content)
    assert re.search(r"Verified / unverified\*\*: \d+/\d+", content)
    assert "Classification breakdown" in content


def test_territory_view_has_no_single_collapsed_percentage_or_badge():
    content = _real_content()
    lines_outside_table = [
        line for line in content.splitlines() if not line.startswith("|")
    ]
    prose = "\n".join(lines_outside_table)
    # No bare top-level "NN% complete"/"NN% done" style summary anywhere outside the per-axis,
    # per-Rule table rows.
    assert not re.search(r"\b\d{1,3}%\s*(complete|done|coverage)\b", prose, re.IGNORECASE)


def test_real_territory_view_is_up_to_date():
    """Load-bearing regression check: the committed file must match a fresh render, not just have
    been correct at generation time."""
    expected = _real_content()
    actual = _OUTPUT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/brainstorm/territory_control_management_view.md is stale -- "
        "run `make territory-control-view`"
    )
