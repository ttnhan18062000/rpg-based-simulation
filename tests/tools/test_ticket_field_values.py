"""Tests for tools/ticket_field_values.py (TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM).

Coverage-honesty requirement (mirrors test_status_drift_check.py's own stated convention): every
check function below has a fixture proving it catches a real violation, not just that it runs on
the happy path.
"""

import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import validate_frontmatter  # noqa: E402
from ticket_field_values import (  # noqa: E402
    LAYER_VALUES,
    PRIORITY_VALUES,
    TIER_VALUES,
    WORKFLOW_STATUS_VALUES,
    check_body_field_enum,
    check_ticket_field_values,
)


def _write_ticket(tmp_path, name, tier="standard", priority="P1"):
    (tmp_path / name).write_text(
        "---\nstatus: historical\n---\n\n"
        f"# {name}\n\n## Title\nFixture\n\n## Status\nDONE\n\n"
        f"## Tier\n{tier}\n\n## Type\nchore\n\n## Priority\n{priority}\n"
    )


def test_canonical_sets_have_expected_values():
    assert TIER_VALUES == frozenset({"hotfix", "standard", "epic"})
    assert PRIORITY_VALUES == frozenset({"P0", "P1", "P2", "P3"})
    assert WORKFLOW_STATUS_VALUES == frozenset(
        {"OPEN", "INPROGRESS", "BLOCKED", "DONE", "EPIC_SCOPED"}
    )


def test_layer_values_is_imported_not_duplicated():
    # Same object, not a copy — proves no second source of truth exists.
    assert LAYER_VALUES is validate_frontmatter.LAYER_VALUES


def test_check_body_field_enum_passes_valid_value():
    body = "## Priority\nP1\n"
    status, evidence = check_body_field_enum(body, "Priority", PRIORITY_VALUES)
    assert status == "PASS"
    assert "P1" in evidence


def test_check_body_field_enum_flags_non_canonical_value():
    # The real corpus drift this module exists to prevent going forward: "P1: High" is not P1.
    body = "## Priority\nP1: High\n"
    status, evidence = check_body_field_enum(body, "Priority", PRIORITY_VALUES)
    assert status == "FAIL"
    assert "P1: High" in evidence


def test_check_body_field_enum_passes_absent_section():
    body = "## Title\nno priority section here\n"
    status, _ = check_body_field_enum(body, "Priority", PRIORITY_VALUES)
    assert status == "PASS"


def test_check_ticket_field_values_passes_valid_ticket(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-VALID.md", tier="standard", priority="P2")
    results = check_ticket_field_values(tmp_path / "TCK-20260101-VALID.md")
    assert len(results) == 1
    assert results[0]["status"] == "PASS"


def test_check_ticket_field_values_flags_bad_priority(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-BADPRI.md", tier="standard", priority="P1: High")
    results = check_ticket_field_values(tmp_path / "TCK-20260101-BADPRI.md")
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "P1: High" in results[0]["evidence"]


def test_check_ticket_field_values_flags_bad_tier(tmp_path):
    _write_ticket(tmp_path, "TCK-20260101-BADTIER.md", tier="urgent", priority="P1")
    results = check_ticket_field_values(tmp_path / "TCK-20260101-BADTIER.md")
    assert len(results) == 1
    assert results[0]["status"] == "FAIL"
    assert "urgent" in results[0]["evidence"]
