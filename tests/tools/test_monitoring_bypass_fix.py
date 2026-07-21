"""Regression tests for the 2026-07-20 agent-orchestration audit's monitoring-bypass findings.

Static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js` and
`.claude/workflows/implement-epic.js` — reuses tests/tools/test_step0_ts_orchestrator.py's and
tests/tools/test_current_run_sidecar_orchestrator.py's established pattern of `Path.read_text()`
against these non-Python source files. The workflow files are never executed (no JS test runner
exists in this repo for `.claude/workflows/*.js`).

Covers:
- implement-ticket.js's Scope phase previously dereferenced `ticketInfo.ticket_id` with no
  null-guard — a null/malformed ticket-scoper response would throw before any monitoring
  machinery (events/pushEvent/writeMonitoring) existed, violating CLAUDE.md's "every run must
  record a monitoring entry" hard rule at exactly the point it exists to protect.
- implement-epic.js had 3 early-return exit paths (INVALID_ARGS, EPIC_CREATED, NOTHING_TO_DO)
  that returned before the batch-monitoring-write agent() call, silently skipping monitoring
  despite docs/ai/workflows.md documenting runs.jsonl/events.jsonl as always-produced artifacts.
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_IMPLEMENT_EPIC_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-epic.js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_implement_ticket_scope_has_null_guard_before_ticket_info_dereference():
    text = _read(_IMPLEMENT_TICKET_PATH)
    guard_idx = text.find("if (!ticketInfo || !ticketInfo.ticket_id)")
    tid_idx = text.find("const tid = ticketInfo.ticket_id")
    assert guard_idx != -1, "null-guard for ticketInfo not found"
    assert tid_idx != -1, "const tid = ticketInfo.ticket_id not found"
    assert guard_idx < tid_idx, "null-guard must appear before the unguarded ticket_id dereference"


def test_implement_ticket_null_guard_writes_monitoring_before_returning():
    text = _read(_IMPLEMENT_TICKET_PATH)
    guard_idx = text.find("if (!ticketInfo || !ticketInfo.ticket_id)")
    assert guard_idx != -1
    # Slice from the guard to the const tid line (the guard block's own closing brace) and
    # confirm a record_run.py write happens inside it, before the block's return statement.
    tid_idx = text.find("const tid = ticketInfo.ticket_id")
    guard_block = text[guard_idx:tid_idx]
    record_idx = guard_block.find("record_run.py")
    return_idx = guard_block.find("return {")
    assert record_idx != -1, "guard block does not write a run record"
    assert return_idx != -1, "guard block does not return"
    assert record_idx < return_idx, "monitoring write must happen before the early return"
    assert "SCOPE_AGENT_FAILED" in guard_block


def test_implement_ticket_null_guard_does_not_reference_forward_declared_helpers():
    # captureTs/writeSidecar/writeMonitoring are all defined later in the file — the guard block
    # must not CALL them, to avoid depending on forward-reference execution order. (The block's own
    # comment explaining this design choice legitimately mentions their names in prose, so this
    # checks for actual invocation syntax, not a bare substring match.)
    text = _read(_IMPLEMENT_TICKET_PATH)
    guard_idx = text.find("if (!ticketInfo || !ticketInfo.ticket_id)")
    tid_idx = text.find("const tid = ticketInfo.ticket_id")
    guard_block = text[guard_idx:tid_idx]
    assert "await captureTs()" not in guard_block
    assert "await writeSidecar(" not in guard_block
    assert "await writeMonitoring(" not in guard_block


def test_implement_epic_invalid_args_writes_monitoring_before_returning():
    text = _read(_IMPLEMENT_EPIC_PATH)
    guard_idx = text.find("if (!folder && !epicId && !request)")
    assert guard_idx != -1
    close_idx = text.find("\n}\n", guard_idx)
    block = text[guard_idx:close_idx]
    record_idx = block.find("record_run.py")
    return_idx = block.find("return {")
    assert record_idx != -1, "INVALID_ARGS block does not write a run record"
    assert return_idx != -1
    assert record_idx < return_idx
    assert "INVALID_ARGS" in block


def test_implement_epic_epic_created_writes_monitoring_before_returning():
    text = _read(_IMPLEMENT_EPIC_PATH)
    guard_idx = text.find("if (discovery.mode === 'request')")
    assert guard_idx != -1
    close_idx = text.find("\n}\n", guard_idx)
    block = text[guard_idx:close_idx]
    record_run_idx = block.find("record_run.py")
    record_events_idx = block.find("record_events.py")
    return_idx = block.find("return {")
    assert record_run_idx != -1, "EPIC_CREATED block does not write a run record"
    assert record_events_idx != -1, "EPIC_CREATED block does not write an event record"
    assert return_idx != -1
    assert record_run_idx < return_idx
    assert record_events_idx < return_idx
    assert "EPIC_CREATED" in block


def test_implement_epic_nothing_to_do_writes_monitoring_before_returning():
    text = _read(_IMPLEMENT_EPIC_PATH)
    guard_idx = text.find("if (ticketIds.length === 0)")
    assert guard_idx != -1
    close_idx = text.find("\n}\n", guard_idx)
    block = text[guard_idx:close_idx]
    record_run_idx = block.find("record_run.py")
    return_idx = block.find("return {")
    assert record_run_idx != -1, "NOTHING_TO_DO block does not write a run record"
    assert return_idx != -1
    assert record_run_idx < return_idx
    assert "NOTHING_TO_DO" in block


def test_implement_epic_early_return_run_ids_do_not_interpolate_raw_agent_text():
    # This file has a documented shell-quote-corruption risk (see implement-ticket.js's
    # classifyChecklistFailure comment) — the 3 new early-monitoring-write blocks must use fixed
    # literal summary strings, not raw discovery.summary/discovery.epic_ticket_path text, embedded
    # directly into a bash single-quoted JSON payload.
    text = _read(_IMPLEMENT_EPIC_PATH)
    assert '"summary":"${discovery.summary}"' not in text
    assert "discovery.summary}\"" not in text.replace('"summary":"${discovery.summary}"', "")
