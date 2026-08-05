"""Tests for wiring a `performance`-tag reminder into implement-ticket.js's Test-phase prompt
and test-scoper.md (TCK-20260805-SKILL-GATE-CONVERSION-DECISION).

Static, raw-source-text-parsing tests against implement-ticket.js and test-scoper.md — reuses
tests/tools/test_document_update_phase_wiring.py's established pattern of Path.read_text()
against these non-Python source files (implement-ticket.js is never executed; no JS test runner
exists for .claude/workflows/*.js).

This is NOT a new gate/phase (unlike Security-Review) — python-performance-optimization's real
verdict shape (PerfRegressionGate, docs/performance/perf_baseline_policy.md §3) is already
enforced through the EXISTING Test phase, gated on test-scoper correctly including
tests/unit/perf/ and tests/perf/ in its scoped pytest command. This wiring exists to make that
inclusion reliable for performance-tagged tickets whose changed files fall outside src/perf/
itself, mirroring WORKFLOW-SECURITY-GATE's own precedent of reading ticketInfo.tags directly as
ground truth (see the `security` tag check at implement-ticket.js:1228-1234) — but as a prompt
enrichment to the existing Test-phase gate, not a new blocking phase or `return {status: ...}`.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_TEST_SCOPER_MD_PATH = _REPO_ROOT / ".claude" / "agents" / "test-scoper.md"


def _read_js() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def _read_test_scoper_md() -> str:
    return _TEST_SCOPER_MD_PATH.read_text(encoding="utf-8")


def test_performance_tag_check_reads_ticket_info_tags_directly():
    """Ground truth must come from ticketInfo.tags directly, mirroring the `security` tag check's
    own precedent — not a re-derived/cached copy."""
    text = _read_js()
    assert "ticketInfo.tags && ticketInfo.tags.includes('performance')" in text


def test_performance_tag_reminder_sits_inside_test_phase_agent_prompt():
    """The conditional reminder must be part of the string passed to the test-scoper agent() call,
    not a separate orchestrator-run step — this is a prompt enrichment of the existing Test phase,
    not a new phase."""
    text = _read_js()
    agent_call_idx = text.find("agentType: 'test-scoper'")
    assert agent_call_idx != -1
    reminder_idx = text.find("This ticket is tagged \\`performance\\`")
    if reminder_idx == -1:
        # Backtick may be unescaped depending on template-literal nesting; fall back to a
        # substring that survives either quoting style.
        reminder_idx = text.find("always include")
    assert reminder_idx != -1, "performance-tag reminder text not found in implement-ticket.js"
    tag_check_idx = text.find("ticketInfo.tags && ticketInfo.tags.includes('performance')")
    assert tag_check_idx != -1
    # Both the conditional check and its reminder text must appear before the agent() call closes
    # (i.e. inside the same prompt template literal), and the tag check must precede the text it
    # gates.
    assert tag_check_idx < reminder_idx < agent_call_idx


def test_performance_tag_reminder_cites_the_real_regression_gate_doc():
    text = _read_js()
    assert "docs/performance/perf_baseline_policy.md" in text


def test_performance_tag_reminder_names_both_perf_test_dirs():
    text = _read_js()
    window_start = text.find("ticketInfo.tags.includes('performance')")
    assert window_start != -1
    window = text[window_start:window_start + 600]
    assert "tests/unit/perf/" in window
    assert "tests/perf/" in window


def test_does_not_introduce_a_new_blocking_status_for_performance():
    """This must stay a prompt enrichment of the existing Test-phase gate — no new
    `return { status: ... }` block keyed on the performance tag (that would make it a second
    gate, duplicating Test, which the ticket's own investigation found unnecessary)."""
    text = _read_js()
    tag_check_idx = text.find("ticketInfo.tags.includes('performance')")
    assert tag_check_idx != -1
    # The next `return { status:` after the tag check should be TESTS_FAILED's own existing
    # return (the pre-existing Test-phase gate), not a new performance-specific one.
    next_return_idx = text.find("return {\n    status:", tag_check_idx)
    assert next_return_idx != -1
    next_return_window = text[next_return_idx:next_return_idx + 120]
    assert "TESTS_FAILED" in next_return_window


def test_test_scoper_md_documents_the_same_rule():
    text = _read_test_scoper_md()
    assert "performance" in text
    assert "tests/unit/perf/" in text
    assert "tests/perf/" in text
    assert "docs/performance/perf_baseline_policy.md" in text


def test_test_scoper_md_rule_sits_in_scoping_rules_section():
    text = _read_test_scoper_md()
    section_idx = text.find("## Scoping Rules")
    next_section_idx = text.find("\n## ", section_idx + 1)
    assert section_idx != -1 and next_section_idx != -1
    section = text[section_idx:next_section_idx]
    assert "performance" in section
