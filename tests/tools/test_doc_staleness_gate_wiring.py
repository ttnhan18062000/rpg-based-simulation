"""Regression tests for wiring tools/gate_checks/doc_staleness_check.py into
.claude/workflows/implement-ticket.js (TCK-20260720-GATE-CHECK-WIRING-DECISIONS).

Static, raw-source-text-parsing tests against implement-ticket.js — reuses
tests/tools/test_monitoring_bypass_fix.py's and test_step0_ts_orchestrator.py's established
pattern of Path.read_text() against this non-Python source file. The workflow file is never
executed (no JS test runner exists in this repo for .claude/workflows/*.js).

doc_staleness_check.py shipped unwired by TCK-20260711-DOC-STALENESS-GATE-CHECK, built after the
2026-W28 retro found 36% of done-checker's first-attempt Verify failures traced to a
behavior-changing src/workflow diff with no docs/ update, caught only reactively 6+ phases later.
This wires it in immediately after Implement returns, mirroring the exact precedent already set
for TAGS_NOT_REGISTERED (pulled forward from Verify to Scope for the identical reason) — including
that precedent's shape of folding the check's outcome into the SAME phase event rather than
emitting a second one, and using the real 'implementer' agent name, not a synthetic pseudo-agent
name outside vocabulary.py's WORKFLOW_AGENTS controlled set.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"


def _read() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def test_doc_staleness_check_is_invoked_between_implement_and_architecture_verify():
    text = _read()
    implement_agent_idx = text.find("{ label: 'implement', schema: IMPL_SCHEMA, agentType: 'implementer' }")
    check_idx = text.find("doc_staleness_check.py")
    arch_verify_idx = text.find("phase('Architecture-Verify')")
    assert implement_agent_idx != -1
    assert check_idx != -1, "doc_staleness_check.py is not invoked anywhere in implement-ticket.js"
    assert arch_verify_idx != -1
    assert implement_agent_idx < check_idx < arch_verify_idx, (
        "doc_staleness_check.py must run after the Implement agent call returns and before "
        "Architecture-Verify — catching the gap as early as files_changed/behavior_changed exist"
    )


def test_doc_staleness_failure_folds_into_the_single_implement_event_not_a_second_one():
    # Mirrors the TAGS_NOT_REGISTERED precedent: one pushEvent('Scope', 'ticket-scoper', ...) call
    # whose status/summary depend on the check outcome, not two separate events.
    text = _read()
    check_idx = text.find("doc_staleness_check.py")
    push_event_calls = [
        i for i in range(check_idx, text.find("phase('Architecture-Verify')"))
        if text.startswith("pushEvent(", i)
    ]
    assert len(push_event_calls) == 1, (
        f"expected exactly one pushEvent call between the doc-staleness check and "
        f"Architecture-Verify, found {len(push_event_calls)}"
    )
    push_event_text = text[push_event_calls[0]:push_event_calls[0] + 200]
    assert "'Implement'" in push_event_text
    assert "'implementer'" in push_event_text, (
        "must use the real 'implementer' agent name (vocabulary.py's WORKFLOW_AGENTS), "
        "not a synthetic pseudo-agent name"
    )


def test_doc_staleness_blocked_status_has_no_reason_code():
    # DOC_STALENESS_BLOCKED disambiguates 1:1 like TAGS_NOT_REGISTERED/PARITY_INCOMPLETE/
    # SECURITY_BLOCKED/TESTS_FAILED/CONFLICTS_DETECTED — reason_code exists only for statuses that
    # collapse multiple distinct causes into one value (DOD_BLOCKED). Adding an unneeded
    # reason_code here would reintroduce exactly the kind of undocumented-field drift
    # TCK-20260720-DOCS-AI-SCHEMA-ACCURACY (sibling ticket) fixed elsewhere in this same file.
    text = _read()
    check_idx = text.find("doc_staleness_check.py")
    arch_verify_idx = text.find("phase('Architecture-Verify')")
    block = text[check_idx:arch_verify_idx]
    push_event_start = block.find("pushEvent(")
    push_event_end = block.find(")\n", push_event_start)
    push_event_call = block[push_event_start:push_event_end]
    # 5 positional args (phase, agent, status, summary, ts) means no reason_code (6th) was passed.
    assert push_event_call.count(",") <= 4, (
        f"pushEvent call appears to pass more than 5 args (possible stray reason_code): "
        f"{push_event_call!r}"
    )


def test_doc_staleness_blocked_writes_monitoring_before_returning():
    text = _read()
    check_idx = text.find("doc_staleness_check.py")
    arch_verify_idx = text.find("phase('Architecture-Verify')")
    block = text[check_idx:arch_verify_idx]
    write_monitoring_idx = block.find("writeMonitoring('DOC_STALENESS_BLOCKED')")
    return_idx = block.find("status: 'DOC_STALENESS_BLOCKED'")
    assert write_monitoring_idx != -1
    assert return_idx != -1
    assert write_monitoring_idx < return_idx


def test_doc_staleness_check_passes_behavior_changed_and_files_changed():
    text = _read()
    invoke_idx = text.find("python3 tools/gate_checks/doc_staleness_check.py")
    assert invoke_idx != -1, "no bash() invocation of doc_staleness_check.py found"
    call_line_start = text.rfind("\n", 0, invoke_idx)
    call_line_end = text.find("\n", invoke_idx)
    call_line = text[call_line_start:call_line_end]
    assert "implementation.behavior_changed" in call_line
    assert "docStalenessFilesArgs" in call_line


def test_docs_to_update_wired_into_doc_staleness_invocation():
    # TCK-20260802-DOC-UPDATE-DISCIPLINE: Investigate's docs_to_update must reach the
    # doc_staleness_check.py invocation (via the --docs-to-update CLI sentinel), purely additive —
    # never replacing implementation.behavior_changed/docStalenessFilesArgs from the test above.
    text = _read()
    invoke_idx = text.find("python3 tools/gate_checks/doc_staleness_check.py")
    call_line_start = text.rfind("\n", 0, invoke_idx)
    call_line_end = text.find("\n", invoke_idx)
    call_line = text[call_line_start:call_line_end]
    assert "docsToUpdateArgs" in call_line
    assert "investigation.docs_to_update" in text[:invoke_idx][-1500:], (
        "investigation.docs_to_update must be read somewhere shortly before the invocation line"
    )
