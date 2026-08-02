"""Regression tests for wiring `make knowledge-index-update` into Finalize
(TCK-20260802-DOC-UPDATE-DISCIPLINE).

Static, raw-source-text-parsing tests against implement-ticket.js — mirrors
tests/tools/test_doc_staleness_gate_wiring.py's established pattern of Path.read_text() against
this non-Python source file (no JS test runner exists in this repo for .claude/workflows/*.js).

CLAUDE.md's After Work rule and docs/guidelines/agent_working_environment.md's Index Lifecycle
Rules both require `make knowledge-index-update` whenever docs/ changes. Confirmed absent from
implement-ticket.js before this ticket (grep returned zero hits) despite docs/REGISTRY.yaml
regeneration (a related but distinct mechanism) already being wired via run_finalize_selfcheck.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"


def _read() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def test_finalize_runs_knowledge_index_update_after_selfcheck():
    text = _read()
    selfcheck_idx = text.find("run_finalize_selfcheck")
    reindex_idx = text.find("make knowledge-index-update")
    final_return_idx = text.rfind("status: 'DONE'")
    assert selfcheck_idx != -1
    assert reindex_idx != -1, "make knowledge-index-update is not wired into implement-ticket.js"
    assert final_return_idx != -1
    assert selfcheck_idx < reindex_idx < final_return_idx, (
        "knowledge-index-update must run after Finalize's own migration self-check and before "
        "the final DONE return"
    )


def test_knowledge_index_refresh_is_conditional_on_docs_changes():
    text = _read()
    reindex_idx = text.find("make knowledge-index-update")
    preceding_block = text[max(0, reindex_idx - 800):reindex_idx]
    assert "git status --porcelain -- docs/" in preceding_block, (
        "the reindex must be gated on an actual docs/ change, not run unconditionally every run"
    )


def test_knowledge_index_refresh_is_fail_open():
    text = _read()
    reindex_idx = text.find("make knowledge-index-update")
    # Scan forward to the next blank-line-delimited block boundary (empty line) to bound the
    # refresh's own if-block without over-including the unrelated code that follows it.
    block_end = text.find("\n\n", reindex_idx)
    block = text[reindex_idx:block_end if block_end != -1 else reindex_idx + 600]
    assert "return {" not in block, (
        "the knowledge-index refresh must never return a new blocking status — fail-open only"
    )
    assert "REINDEX_FAILED" in block, "failure must be caught and logged, not left to throw"


def test_knowledge_index_refresh_is_orchestrator_bash_not_agent_prompt():
    text = _read()
    finalize_agent_start = text.find("phase('Finalize')")
    finalize_agent_end = text.find("{ label: 'finalize' }")
    assert finalize_agent_start != -1
    assert finalize_agent_end != -1
    finalize_prompt_block = text[finalize_agent_start:finalize_agent_end]
    assert "make knowledge-index-update" not in finalize_prompt_block, (
        "the reindex must be an orchestrator-run bash() call, not text inside the Finalize "
        "agent's own prompt — a bare, non-phase()-anchored agent-prompt bash instruction has "
        "been observed to silently not execute (see docs/ai/ticket-lifecycle.md's Reliability "
        "caveat for the post-Test cleanup checkpoint)"
    )
    reindex_idx = text.find("make knowledge-index-update")
    assert reindex_idx > finalize_agent_end, (
        "the reindex call must come after the Finalize agent() call returns"
    )
