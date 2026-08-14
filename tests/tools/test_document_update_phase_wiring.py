"""Tests for wiring the Document-Update phase + doc-updater agent into
.claude/workflows/implement-ticket.js (TCK-20260803-DOC-UPDATER-CORE-WIRING).

Static, raw-source-text-parsing tests against implement-ticket.js — reuses
tests/tools/test_doc_staleness_gate_wiring.py's established pattern of Path.read_text() against
this non-Python source file. The workflow file is never executed (no JS test runner exists in
this repo for .claude/workflows/*.js).

docs/architecture/doc_updater_agent.md's Decision section requires the new phase to sit strictly
between Implement's agent() call and the existing doc_staleness_check.py gate — not after it —
with the orchestrator merging doc-updater's own reported files into the list that gate evaluates
before it runs. check_doc_staleness()'s own internal pass/fail logic is unchanged; only its input
is. No new blocking `return { status: ... }` is introduced for this phase — a doc-updater blocker
is reported via a `failed`-status event only, mirroring Parity's non-fatal shape.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_WORKFLOWS_MD_PATH = _REPO_ROOT / "docs" / "ai" / "workflows.md"
_SYSTEM_OVERVIEW_MD_PATH = _REPO_ROOT / "docs" / "ai" / "system_overview.md"


def _read() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def test_document_update_phase_between_implement_and_doc_staleness_check():
    text = _read()
    implement_agent_close_idx = text.find("{ label: 'implement', schema: IMPL_SCHEMA, agentType: 'implementer' }")
    doc_update_phase_idx = text.find("phase('Document-Update')")
    doc_staleness_idx = text.find("doc_staleness_check.py")
    assert implement_agent_close_idx != -1
    assert doc_update_phase_idx != -1, "phase('Document-Update') not found in implement-ticket.js"
    assert doc_staleness_idx != -1
    assert implement_agent_close_idx < doc_update_phase_idx < doc_staleness_idx, (
        "phase('Document-Update') must land strictly between Implement's agent() call and the "
        "doc-staleness gate — not after it"
    )


def test_document_update_files_changed_merged_into_doc_staleness_args():
    text = _read()
    invoke_idx = text.find("python3 tools/gate_checks/doc_staleness_check.py")
    assert invoke_idx != -1
    window = text[:invoke_idx][-1500:]
    assert "implementation.files_changed" in window, (
        "the merged array feeding docStalenessFilesArgs must still include implementation.files_changed"
    )
    assert "docUpdate.docs_updated" in window, (
        "the merged array feeding docStalenessFilesArgs must also include doc-updater's own reported files"
    )


def test_document_update_runs_unconditionally_no_hotfix_guard():
    text = _read()
    doc_update_phase_idx = text.find("phase('Document-Update')")
    push_event_idx = text.find("pushEvent(\n  'Document-Update'")
    assert doc_update_phase_idx != -1
    assert push_event_idx != -1
    block = text[doc_update_phase_idx:push_event_idx]
    assert "if (tier !== 'hotfix')" not in block
    assert "if(tier !== 'hotfix')" not in block

    # Confirm the block does not fall inside the pre-Implement `if (tier !== 'hotfix') { ... }`
    # standard-tier-only span (Investigate/Plan/Review), which closes before Implement begins.
    tier_conditional_open_idx = text.find("if (tier !== 'hotfix') {")
    tier_conditional_close_idx = text.find("\n} else {", tier_conditional_open_idx)
    assert tier_conditional_open_idx != -1
    assert tier_conditional_close_idx != -1
    assert not (tier_conditional_open_idx < doc_update_phase_idx < tier_conditional_close_idx), (
        "Document-Update must not fall inside the standard-tier-only Investigate/Plan/Review span"
    )


def test_document_update_failure_does_not_return_blocking_status():
    text = _read()
    doc_update_phase_idx = text.find("phase('Document-Update')")
    doc_staleness_idx = text.find("doc_staleness_check.py")
    assert doc_update_phase_idx != -1
    assert doc_staleness_idx != -1
    block = text[doc_update_phase_idx:doc_staleness_idx]
    assert "return {" not in block, (
        "Document-Update must never return a blocking status — a blocker is reported via a "
        "'failed'-status pushEvent only, mirroring Parity's non-fatal shape"
    )


def test_document_update_pushevent_status_reads_blocker_field():
    text = _read()
    push_event_idx = text.find("pushEvent(\n  'Document-Update'")
    assert push_event_idx != -1, "expected a pushEvent('Document-Update', ...) call"
    call_text = text[push_event_idx:push_event_idx + 300]
    assert "docUpdate.blocker ? 'failed' : 'ok'" in call_text, (
        "the pushEvent status argument must literally read docUpdate.blocker ? 'failed' : 'ok' — "
        "not a placeholder, not derived from docs_skipped's length or contents"
    )
    assert "docs_skipped.length" not in call_text
    assert "docs_skipped" not in call_text, (
        "a non-empty docs_skipped must never itself produce a 'failed' status — only a set blocker may"
    )


def test_document_update_phase_appears_in_workflows_md_table():
    text = _WORKFLOWS_MD_PATH.read_text(encoding="utf-8")
    implement_ticket_idx = text.find("### `implement-ticket`")
    assert implement_ticket_idx != -1
    next_section_idx = text.find("\n### ", implement_ticket_idx + 1)
    section = text[implement_ticket_idx:next_section_idx if next_section_idx != -1 else len(text)]
    assert "Document-Update" in section
    assert "doc-updater" in section


def test_document_update_appears_in_system_overview_hotfix_line():
    text = _SYSTEM_OVERVIEW_MD_PATH.read_text(encoding="utf-8")
    hotfix_line_idx = text.find("| `hotfix` |")
    assert hotfix_line_idx != -1, "hotfix pipeline summary row not found in system_overview.md"
    line_end = text.find("\n", hotfix_line_idx)
    hotfix_line = text[hotfix_line_idx:line_end]
    assert "Document-Update" in hotfix_line
