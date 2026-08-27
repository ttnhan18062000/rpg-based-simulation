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

    # TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX: structural invariants, not a literal line-number
    # list — this exact drift (implement-ticket.js edits shifting FINALIZE_INCOMPLETE's call-site
    # line numbers) has forced 8 separate hotfix tickets since 2026-08-02. Line position may drift
    # freely; the real invariants are (a) exactly 2 distinct, ascending call sites, and (b) the two
    # sites are genuinely different code paths, not an accidental duplicate of the same one.
    finalize_incomplete_sites = by_value["FINALIZE_INCOMPLETE"]["call_sites"]
    assert len(finalize_incomplete_sites) == 2, (
        f"expected exactly 2 distinct FINALIZE_INCOMPLETE call sites, found "
        f"{len(finalize_incomplete_sites)}: {finalize_incomplete_sites}"
    )
    assert finalize_incomplete_sites == sorted(finalize_incomplete_sites), (
        "call sites must be in strictly ascending source order"
    )
    assert len(set(finalize_incomplete_sites)) == 2, "call sites must be distinct, not duplicated"

    finalize_incomplete_contexts = by_value["FINALIZE_INCOMPLETE"]["contexts"]
    assert len(finalize_incomplete_contexts) == 2
    assert all(c is not None for c in finalize_incomplete_contexts), (
        f"expected a message-literal context marker at both call sites, got "
        f"{finalize_incomplete_contexts}"
    )
    assert len(set(finalize_incomplete_contexts)) == 2, (
        f"the two FINALIZE_INCOMPLETE call sites must be genuinely distinct code paths (different "
        f"message text), not an accidental duplicate of the same branch: "
        f"{finalize_incomplete_contexts}"
    )

    assert by_value["DONE"]["kind"] == "literal"
    assert by_value["NEEDS_CHANGES"]["kind"] == "verdict_derived"
    assert by_value["BLOCKED"]["kind"] == "verdict_derived"
    assert by_value["SCOPE_AGENT_FAILED"]["kind"] == "bypass"


def test_call_site_detection_tolerates_unrelated_line_insertion_above(tmp_path):
    """TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX: proves the structural invariants above survive
    an unrelated line inserted above both FINALIZE_INCOMPLETE call sites — the exact class of edit
    that broke the old literal-line-number assertions 8 times since 2026-08-02."""
    base_fixture = """\
if (finalizeResults === null) {
  pushEvent('Finalize', 'finalizer', 'failed', 'parse failed')
  await writeMonitoring('FINALIZE_INCOMPLETE')
  return {
    status: 'FINALIZE_INCOMPLETE',
    message: 'Finalize self-check output could not be parsed — treating as incomplete.',
  }
}

const finalizeFailures = finalizeResults.filter(r => r.status === 'FAIL')
if (finalizeFailures.length > 0) {
  await writeMonitoring('FINALIZE_INCOMPLETE')
  return {
    status: 'FINALIZE_INCOMPLETE',
    message: 'Finalize completed its steps but the post-migration self-check found a discrepancy.',
  }
}
"""
    shifted_fixture = "// an unrelated comment line inserted above everything\n" + base_fixture

    def _finalize_incomplete_invariants(fixture_text: str) -> tuple[list[int], list[str | None]]:
        fixture_path = tmp_path / "fixture.js"
        fixture_path.write_text(fixture_text, encoding="utf-8")
        statuses = extract_all_terminal_statuses(fixture_path)
        by_value = {e["value"]: e for e in statuses}
        return by_value["FINALIZE_INCOMPLETE"]["call_sites"], by_value["FINALIZE_INCOMPLETE"]["contexts"]

    base_sites, base_contexts = _finalize_incomplete_invariants(base_fixture)
    shifted_sites, shifted_contexts = _finalize_incomplete_invariants(shifted_fixture)

    # The raw line numbers DO shift (proving the fixture setup itself is meaningful) ...
    assert shifted_sites != base_sites
    assert all(s + 1 == b for s, b in zip(base_sites, shifted_sites)), (
        "expected the inserted line to shift every call site down by exactly 1"
    )
    # ... but the structural invariants a real test would assert do NOT change.
    for sites, contexts in ((base_sites, base_contexts), (shifted_sites, shifted_contexts)):
        assert len(sites) == 2
        assert sites == sorted(sites)
        assert len(set(sites)) == 2
        assert len(contexts) == 2
        assert all(c is not None for c in contexts)
        assert len(set(contexts)) == 2
    assert base_contexts == shifted_contexts, "context markers themselves must be line-position-independent"
