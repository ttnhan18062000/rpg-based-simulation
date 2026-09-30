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


# ---------------------------------------------------------------------------
# CLI entry point (TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT)
# ---------------------------------------------------------------------------

import subprocess

_MODULE_PATH = _TOOLS_DIR / "ticket_field_values.py"


def test_cli_prints_readable_output_and_exits_zero_on_pass(tmp_path):
    _write_ticket(tmp_path, "TCK-CLI-PASS.md", tier="standard", priority="P1")
    ticket_path = tmp_path / "TCK-CLI-PASS.md"
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), str(ticket_path)], capture_output=True, text=True,
    )
    assert result.stdout.strip(), "expected non-empty stdout -- silence is exactly the regression"
    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_cli_prints_readable_output_and_exits_nonzero_on_fail(tmp_path):
    _write_ticket(tmp_path, "TCK-CLI-FAIL.md", tier="urgent", priority="P1")
    ticket_path = tmp_path / "TCK-CLI-FAIL.md"
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), str(ticket_path)], capture_output=True, text=True,
    )
    assert result.stdout.strip()
    assert result.returncode != 0
    assert "FAIL" in result.stdout
    assert "urgent" in result.stdout


def test_cli_help_produces_usage_text_not_silence():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--help"], capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()


def test_cli_still_importable_and_callable_as_plain_function(tmp_path):
    """Pins the Scope constraint: existing python3 -c call sites (check_ticket_field_values(path))
    must keep working unchanged, not routed through the new CLI."""
    assert callable(check_ticket_field_values)
    _write_ticket(tmp_path, "TCK-IMPORT-TEST.md", tier="standard", priority="P1")
    ticket_path = tmp_path / "TCK-IMPORT-TEST.md"
    result = check_ticket_field_values(ticket_path)
    assert isinstance(result, list)
    assert result[0]["status"] == "PASS"


# ── TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES ────────────────────────────────────────────

from ticket_field_values import (  # noqa: E402
    DISPOSITION_VALUES,
    check_disposition_fields,
    check_disposition_rationale,
)
from generate_registry import parse_body_section  # noqa: E402

_DISPOSITION_BODY = (
    "## Tier\nstandard\n\n## Disposition\n{value}\n\n## Disposition Rationale\n{rationale}\n\n## Files Changed\nNone.\n"
)


def test_disposition_values_are_the_five_documented_ones():
    assert DISPOSITION_VALUES == {"STALE-PREMISE", "NO-MECHANISM", "DUPLICATE", "SUPERSEDED", "WONT-DO"}


def test_disposition_and_rationale_sections_parse_independently():
    """Pins the two-section shape: `^## Disposition\\s*\\n` must not swallow or match the
    `## Disposition Rationale` heading, in either direction."""
    body = _DISPOSITION_BODY.format(value="STALE-PREMISE", rationale="Premise false since 791e6bf6b.")
    assert parse_body_section(body, "Disposition") == "STALE-PREMISE"
    assert parse_body_section(body, "Disposition Rationale") == "Premise false since 791e6bf6b."


def test_no_disposition_section_is_not_applicable():
    assert check_disposition_fields("## Tier\nstandard\n")[0] == "NA"


def test_valid_disposition_with_each_evidence_form_passes():
    for rationale in (
        "Premise false since 791e6bf6b.",
        "See src/domains/demographics/cohort.py:377 for the arithmetic.",
        "Compile output:\n```\ncamps=2 regions=8\n```",
    ):
        body = _DISPOSITION_BODY.format(value="STALE-PREMISE", rationale=rationale)
        assert check_disposition_fields(body)[0] == "PASS", rationale


def test_unknown_disposition_value_fails():
    body = _DISPOSITION_BODY.format(value="NOT-A-VALUE", rationale="Premise false since 791e6bf6b.")
    status, evidence = check_disposition_fields(body)
    assert status == "FAIL" and "NOT-A-VALUE" in evidence


def test_empty_disposition_value_fails():
    assert check_disposition_fields("## Disposition\n\n## Disposition Rationale\nsee 791e6bf6b\n")[0] == "FAIL"


def test_disposition_without_rationale_section_fails():
    status, evidence = check_disposition_fields("## Disposition\nSTALE-PREMISE\n")
    assert status == "FAIL" and "missing" in evidence


def test_empty_rationale_fails():
    status, evidence = check_disposition_rationale("## Disposition Rationale\n\n## Files Changed\nNone.\n")
    assert status == "FAIL" and "empty" in evidence


def test_uncited_rationale_fails():
    body = _DISPOSITION_BODY.format(value="WONT-DO", rationale="It just is not worth doing, trust me.")
    status, evidence = check_disposition_fields(body)
    assert status == "FAIL" and "no evidence" in evidence


def test_english_word_that_looks_like_hex_is_not_a_sha():
    body = _DISPOSITION_BODY.format(value="WONT-DO", rationale="We decided this is defaced beyond repair.")
    assert check_disposition_fields(body)[0] == "FAIL"


def test_check_ticket_field_values_rejects_bad_disposition(tmp_path):
    p = tmp_path / "t.md"
    p.write_text(
        "---\nstatus: historical\n---\n\n# t\n\n## Tier\nstandard\n\n## Priority\nP1\n\n"
        "## Disposition\nBOGUS\n\n## Disposition Rationale\nsee 791e6bf6b\n",
        encoding="utf-8",
    )
    result = check_ticket_field_values(p)
    assert len(result) == 1 and result[0]["status"] == "FAIL" and "BOGUS" in result[0]["evidence"]


def test_check_ticket_field_values_unchanged_without_disposition(tmp_path):
    _write_ticket(tmp_path, "plain.md")
    result = check_ticket_field_values(tmp_path / "plain.md")
    assert result[0]["status"] == "PASS" and "Disposition" not in result[0]["evidence"]
