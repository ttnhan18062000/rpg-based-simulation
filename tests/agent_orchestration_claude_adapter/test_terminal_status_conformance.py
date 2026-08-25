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

    # TCK-20260824-TERMINAL-STATUS-STRUCTURAL-FIX: structural invariants, not a literal line-number
    # list — see the sibling assertion in test_terminal_status_extractor.py for the full rationale
    # (this exact drift has forced 8 separate hotfix tickets since 2026-08-02).
    finalize_incomplete_sites = live_finalize_incomplete["call_sites"]
    assert len(finalize_incomplete_sites) == 2, (
        f"expected exactly 2 distinct FINALIZE_INCOMPLETE call sites, found "
        f"{len(finalize_incomplete_sites)}: {finalize_incomplete_sites}"
    )
    assert finalize_incomplete_sites == sorted(finalize_incomplete_sites), (
        "call sites must be in strictly ascending source order"
    )
    assert len(set(finalize_incomplete_sites)) == 2, "call sites must be distinct, not duplicated"

    finalize_incomplete_contexts = live_finalize_incomplete["contexts"]
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
