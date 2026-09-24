"""Tests for the combined cross-domain view in
tools/semantic_control_plane/generate_territory_control_view.py::render_cross_domain.

TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW. Mirrors test_territory_control_view.py's own
structure/conventions. AC4: the combined view must render both domains with raw mapped/unmapped
and verified/unverified counts alongside the classification breakdown, never a bare percentage.
AC7: Combat's real, mixed classification result (PARTIAL/UNKNOWN, never all-SUPPORTED) must never
be smoothed into a manufactured clean contrast against Territory.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from tools.mechanism_registry.registry import MechanismRegistry
from tools.semantic_control_plane.generate_territory_control_view import render_cross_domain

REPO_ROOT = Path(__file__).resolve().parents[3]
_RULE_MECHANISM_EDGES_PATH = REPO_ROOT / "registries" / "rule_mechanism_edges.yaml"
_CLASSIFICATIONS_PATH = REPO_ROOT / "registries" / "rule_classifications.yaml"
_OUTPUT_PATH = REPO_ROOT / "docs" / "brainstorm" / "cross_domain_management_view.md"

_TERR_RULE_IDS = ["TERR-01", "TERR-02", "TERR-03", "TERR-05"]
_COMBAT_RULE_IDS = [
    "CONFLICT-01", "PERC-01", "KNOW-01", "AGENCY-01", "AGENCY-02", "AGENCY-04",
    "LIFE-01", "LIFE-02", "BODY-07", "OWN-02", "CAP-01", "ECOL-04",
]


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _real_content() -> str:
    rule_mechanism_data = _load_yaml(_RULE_MECHANISM_EDGES_PATH)
    classifications_data = _load_yaml(_CLASSIFICATIONS_PATH)
    return render_cross_domain(rule_mechanism_data, classifications_data, MechanismRegistry())


def test_cross_domain_view_renders_both_domains():
    content = _real_content()
    assert "## Territory / Control" in content
    assert "## Combat / Conflict" in content
    for rule_id in _TERR_RULE_IDS + _COMBAT_RULE_IDS:
        assert f"`{rule_id}`" in content, f"missing {rule_id} in the combined view"


def test_cross_domain_view_shows_raw_counts_not_bare_percentage():
    content = _real_content()
    assert re.search(r"Mapped / unmapped \(combined\)\*\*: \d+/\d+", content)
    assert re.search(r"Verified / unverified \(combined\)\*\*: \d+/\d+", content)
    assert "Classification breakdown (combined)" in content
    # Per-domain sections also show their own raw counts, not just the combined banner.
    assert re.search(r"Mapped / unmapped\*\*: \d+/\d+", content)
    assert re.search(r"Verified / unverified\*\*: \d+/\d+", content)

    lines_outside_table = [line for line in content.splitlines() if not line.startswith("|")]
    prose = "\n".join(lines_outside_table)
    assert not re.search(r"\b\d{1,3}%\s*(complete|done|coverage)\b", prose, re.IGNORECASE)


def test_combat_mixed_realization_is_not_smoothed_into_a_clean_result():
    """AC7: Combat's real mapping must surface at least one non-SUPPORTED classification and at
    least one UNKNOWN -- never quietly 'cleaned up' into an all-SUPPORTED result later."""
    rule_mechanism_data = _load_yaml(_RULE_MECHANISM_EDGES_PATH)
    classifications_data = _load_yaml(_CLASSIFICATIONS_PATH)
    classifications = {
        record["rule_id"]: record["classification"]
        for record in classifications_data.get("classifications", []) or []
    }

    combat_classifications = {
        rule_id: classifications.get(rule_id, "UNKNOWN") for rule_id in _COMBAT_RULE_IDS
    }
    assert any(c != "SUPPORTED" for c in combat_classifications.values()), (
        "Combat's real mapping must not be all-SUPPORTED"
    )
    assert "UNKNOWN" in combat_classifications.values(), (
        "CONFLICT-01/ECOL-04 must stay UNKNOWN, not be forced into a row"
    )


def test_real_cross_domain_view_is_up_to_date():
    """Load-bearing regression check: the committed file must match a fresh render, not just have
    been correct at generation time."""
    expected = _real_content()
    actual = _OUTPUT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/brainstorm/cross_domain_management_view.md is stale -- "
        "run `make cross-domain-management-view`"
    )
