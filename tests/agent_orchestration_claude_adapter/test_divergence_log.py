"""Divergence-log parser and human-approval enforcement tests
(TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, AC #4, test_plan item 6).

Verifies a divergence entry lacking the defined reviewer+date marker format does NOT suppress a
conformance failure; an entry WITH a correctly-formatted marker DOES suppress it. Covers both a
positive and a negative fixture case per test_plan's explicit instruction that this is the single
largest net-new behavior this ticket defines.
"""
from __future__ import annotations

from pathlib import Path

from tools.agent_orchestration_claude_adapter.divergence_log import is_approved, load_divergences

_WELL_FORMED_ENTRY = """\
## terminal_status:SOME_STATUS
Axis: terminal_status
Contract-value: absent
Live-value: SOME_STATUS
Rationale: legacy status kept for backward compatibility during migration.
Approved-by: jane.reviewer
Approved-date: 2026-07-22
Status: RATIFIED
"""

_MISSING_APPROVED_BY_ENTRY = """\
## terminal_status:SOME_STATUS
Axis: terminal_status
Contract-value: absent
Live-value: SOME_STATUS
Rationale: legacy status kept for backward compatibility during migration.
Approved-date: 2026-07-22
Status: RATIFIED
"""

_MISSING_APPROVED_DATE_ENTRY = """\
## terminal_status:SOME_STATUS
Axis: terminal_status
Contract-value: absent
Live-value: SOME_STATUS
Rationale: legacy status kept for backward compatibility during migration.
Approved-by: jane.reviewer
Status: RATIFIED
"""

_DEFERRED_STATUS_ENTRY = """\
## terminal_status:SOME_STATUS
Axis: terminal_status
Contract-value: absent
Live-value: SOME_STATUS
Rationale: legacy status kept for backward compatibility during migration.
Approved-by: jane.reviewer
Approved-date: 2026-07-22
Status: DEFERRED
"""

_MALFORMED_DATE_ENTRY = """\
## terminal_status:SOME_STATUS
Axis: terminal_status
Contract-value: absent
Live-value: SOME_STATUS
Rationale: legacy status kept for backward compatibility during migration.
Approved-by: jane.reviewer
Approved-date: not-a-date
Status: RATIFIED
"""


def _write_and_load(tmp_path: Path, content: str):
    path = tmp_path / "intentional-divergences.md"
    path.write_text(content, encoding="utf-8")
    return load_divergences(path)


def test_well_formed_entry_is_parsed_with_all_fields(tmp_path):
    divergences = _write_and_load(tmp_path, _WELL_FORMED_ENTRY)

    assert len(divergences) == 1
    d = divergences[0]
    assert d.axis == "terminal_status"
    assert d.identifier == "SOME_STATUS"
    assert d.approved_by == "jane.reviewer"
    assert d.approved_date == "2026-07-22"
    assert d.status == "RATIFIED"


def test_well_formed_entry_suppresses_a_matching_mismatch(tmp_path):
    divergences = _write_and_load(tmp_path, _WELL_FORMED_ENTRY)
    assert is_approved(divergences, axis="terminal_status", value="SOME_STATUS") is True


def test_missing_approved_by_does_not_suppress(tmp_path):
    divergences = _write_and_load(tmp_path, _MISSING_APPROVED_BY_ENTRY)
    assert is_approved(divergences, axis="terminal_status", value="SOME_STATUS") is False


def test_missing_approved_date_does_not_suppress(tmp_path):
    divergences = _write_and_load(tmp_path, _MISSING_APPROVED_DATE_ENTRY)
    assert is_approved(divergences, axis="terminal_status", value="SOME_STATUS") is False


def test_deferred_status_does_not_suppress(tmp_path):
    divergences = _write_and_load(tmp_path, _DEFERRED_STATUS_ENTRY)
    assert is_approved(divergences, axis="terminal_status", value="SOME_STATUS") is False


def test_malformed_approved_date_does_not_suppress(tmp_path):
    divergences = _write_and_load(tmp_path, _MALFORMED_DATE_ENTRY)
    assert is_approved(divergences, axis="terminal_status", value="SOME_STATUS") is False


def test_non_matching_axis_or_value_does_not_suppress(tmp_path):
    divergences = _write_and_load(tmp_path, _WELL_FORMED_ENTRY)
    assert is_approved(divergences, axis="phase_order", value="SOME_STATUS") is False
    assert is_approved(divergences, axis="terminal_status", value="OTHER_STATUS") is False


def test_empty_divergence_log_has_no_entries_and_approves_nothing(tmp_path):
    path = tmp_path / "intentional-divergences.md"
    path.write_text("# Intentional Divergences\n\nNo entries yet.\n", encoding="utf-8")
    divergences = load_divergences(path)
    assert divergences == []
    assert is_approved(divergences, axis="terminal_status", value="ANYTHING") is False


def test_real_committed_divergence_log_has_zero_entries():
    repo_root = Path(__file__).parent.parent.parent
    real_path = repo_root / "agent-orchestration" / "intentional-divergences.md"
    divergences = load_divergences(real_path)
    assert divergences == [], (
        "this ticket's own build must ship with zero divergence entries (AC #5) — "
        f"found {len(divergences)}"
    )
