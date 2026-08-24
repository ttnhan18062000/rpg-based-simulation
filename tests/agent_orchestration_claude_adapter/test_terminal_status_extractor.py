"""Live terminal-status extraction tests (TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER).

Covers test_plan.md items 3, 4, 5: the literal-call-site extractor, the verdict-derived fixed
constant + live call-site count, and the SCOPE_AGENT_FAILED bypass-handling non-silent-omission
guard.
"""
from __future__ import annotations

from pathlib import Path

from tools.agent_orchestration_claude_adapter.terminal_status_extractor import (
    count_verdict_derived_call_sites,
    extract_all_terminal_statuses,
    extract_bypass_statuses,
    extract_literal_statuses,
    extract_verdict_derived_statuses,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_JS_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"

_EXPECTED_LITERAL_VALUES_MULTISET = [
    "CONFLICTS_DETECTED",
    "TAGS_NOT_REGISTERED",
    "EPIC_SCOPED",
    "NEEDS_HUMAN_INPUT",
    "DOC_STALENESS_BLOCKED",
    "TESTS_FAILED",
    "TEST_SCOPE_COVERAGE_FAILED",
    "DATA_RUNS_CLEAN_FAILED",
    "PARITY_INCOMPLETE",
    "SECURITY_BLOCKED",
    "DOD_BLOCKED",
    "FINALIZE_INCOMPLETE",
    "FINALIZE_INCOMPLETE",
    "DONE",
]


def test_terminal_status_extractor_finds_all_14_literal_call_sites():
    """Was 13 (TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER); TEST_SCOPE_COVERAGE_FAILED added
    2026-08-18 by TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP — a genuine new terminal
    status, not drift."""
    entries = extract_literal_statuses(_WORKFLOW_JS_PATH)

    assert len(entries) == 14, f"expected 14 literal call sites, found {len(entries)}"
    assert sorted(e["value"] for e in entries) == sorted(_EXPECTED_LITERAL_VALUES_MULTISET)
    assert all(e["kind"] == "literal" for e in entries)

    distinct_values = {e["value"] for e in entries}
    assert len(distinct_values) == 13, (
        f"expected 13 distinct literal values (FINALIZE_INCOMPLETE deduping to one value from "
        f"two call sites), got {len(distinct_values)}: {sorted(distinct_values)}"
    )

    finalize_incomplete_sites = [e for e in entries if e["value"] == "FINALIZE_INCOMPLETE"]
    assert len(finalize_incomplete_sites) == 2, (
        "FINALIZE_INCOMPLETE must appear as two separate call-site entries here, not silently "
        "deduped away and not double-counted as a conflict"
    )


def test_terminal_status_extractor_finds_verdict_derived_needs_changes_and_blocked():
    entries = extract_verdict_derived_statuses()

    assert {e["value"] for e in entries} == {"NEEDS_CHANGES", "BLOCKED"}
    assert all(e["kind"] == "verdict_derived" for e in entries)

    live_call_site_count = count_verdict_derived_call_sites(_WORKFLOW_JS_PATH)
    assert live_call_site_count == 2, (
        f"expected 2 live writeMonitoring(<var>.verdict) call sites (review.verdict at :582, "
        f"archVerify.verdict at :760), found {live_call_site_count}"
    )


def test_scope_agent_failed_handling_is_an_explicit_documented_decision():
    bypass_entries = extract_bypass_statuses(_WORKFLOW_JS_PATH)

    assert any(e["value"] == "SCOPE_AGENT_FAILED" for e in bypass_entries), (
        "SCOPE_AGENT_FAILED bypasses writeMonitoring() entirely (raw bash()-embedded "
        "record_run.py --data call) — it must be explicitly captured by extract_bypass_statuses, "
        "not silently omitted from the true terminal-status vocabulary"
    )
    assert all(e["kind"] == "bypass" for e in bypass_entries)

    all_statuses = extract_all_terminal_statuses(_WORKFLOW_JS_PATH)
    scope_agent_failed = [e for e in all_statuses if e["value"] == "SCOPE_AGENT_FAILED"]
    assert len(scope_agent_failed) == 1
    assert scope_agent_failed[0]["kind"] == "bypass"


def test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count():
    all_statuses = extract_all_terminal_statuses(_WORKFLOW_JS_PATH)

    assert len(all_statuses) == 16, (
        f"expected 16 distinct terminal-status values (13 literal + 2 verdict-derived + 1 "
        f"bypass), got {len(all_statuses)}: {sorted(e['value'] for e in all_statuses)}"
    )

    by_value = {e["value"]: e for e in all_statuses}
    assert by_value["FINALIZE_INCOMPLETE"]["call_sites"] == [1546, 1558]
    assert by_value["DONE"]["kind"] == "literal"
    assert by_value["NEEDS_CHANGES"]["kind"] == "verdict_derived"
    assert by_value["BLOCKED"]["kind"] == "verdict_derived"
    assert by_value["SCOPE_AGENT_FAILED"]["kind"] == "bypass"
