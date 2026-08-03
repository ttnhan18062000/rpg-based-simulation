"""Terminal-status conformance test: LIVE `.claude/workflows/implement-ticket.js` extraction vs.
`agent-orchestration/terminal-statuses.yaml` contract data (TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER,
AC #3).

Asserts full match as a set of (value, kind) pairs — order-independent, since terminal statuses
are an unordered set, not a sequence like phase order. Because
agent-orchestration/terminal-statuses.yaml was authored directly from this same live extraction
(TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER Step 1), this test is expected to pass with zero
divergence entries needed.

Any per-value mismatch is checked against `divergence_log.is_approved()` (axis="terminal_status",
value=<the status value>) before hard-failing — see
`agent-orchestration/intentional-divergences.md` for the human-approval mechanism.
"""
from __future__ import annotations

from pathlib import Path

from tools.agent_orchestration_claude_adapter.divergence_log import is_approved, load_divergences
from tools.agent_orchestration_claude_adapter.terminal_status_extractor import (
    extract_all_terminal_statuses,
)
from tools.agent_orchestration_claude_adapter.terminal_status_loader import load_terminal_statuses

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_JS_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_DIVERGENCE_LOG_PATH = _REPO_ROOT / "agent-orchestration" / "intentional-divergences.md"


def _as_value_kind_pairs(statuses: list[dict]) -> set[tuple[str, str]]:
    return {(entry["value"], entry["kind"]) for entry in statuses}


def test_terminal_status_conformance_full_match_both_directions():
    live_statuses = extract_all_terminal_statuses(_WORKFLOW_JS_PATH)
    contract_statuses = load_terminal_statuses(_REPO_ROOT)

    live_pairs = _as_value_kind_pairs(live_statuses)
    contract_pairs = _as_value_kind_pairs(contract_statuses)

    missing_from_contract = live_pairs - contract_pairs
    missing_from_live = contract_pairs - live_pairs

    if missing_from_contract or missing_from_live:
        divergences = load_divergences(_DIVERGENCE_LOG_PATH)
        mismatched_values = {value for value, _kind in missing_from_contract | missing_from_live}
        unapproved = {
            value for value in mismatched_values
            if not is_approved(divergences, axis="terminal_status", value=value)
        }
        assert not unapproved, (
            f"terminal-status mismatch not covered by a human-approved entry in "
            f"{_DIVERGENCE_LOG_PATH}: missing_from_contract={missing_from_contract}, "
            f"missing_from_live={missing_from_live}, unapproved values={unapproved}"
        )


def test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides():
    live_statuses = extract_all_terminal_statuses(_WORKFLOW_JS_PATH)
    contract_statuses = load_terminal_statuses(_REPO_ROOT)

    live_values = [e["value"] for e in live_statuses]
    contract_values = [e["value"] for e in contract_statuses]

    assert live_values.count("FINALIZE_INCOMPLETE") == 1
    assert contract_values.count("FINALIZE_INCOMPLETE") == 1

    live_finalize_incomplete = next(e for e in live_statuses if e["value"] == "FINALIZE_INCOMPLETE")
    assert live_finalize_incomplete["call_sites"] == [1380, 1392]
