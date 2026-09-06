"""Gate-policy conformance test: LIVE `.claude/workflows/implement-ticket.js` extraction vs.
`agent-orchestration/gate-policy.yaml` contract data
(TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST, AC #1).

Mirrors `test_terminal_status_conformance.py`'s exact structure: diffs live -> contract (never the
reverse) as a set of `(phase, gate_type, on_fail_status)` triples (order-independent, since
`on_fail_status` collapses to a sorted tuple — Review/Architecture-Verify's 2-value
verdict-passthrough sets must compare equal regardless of enum declaration order). Any mismatch is
checked against `divergence_log.is_approved()` (axis="gate_policy", value=<phase>) before
hard-failing.
"""
from __future__ import annotations

from pathlib import Path

from tools.agent_orchestration.loader import (
    _GATE_TYPE_EXTRA_KEYS,
    _REQUIRED_GATE_ENTRY_KEYS,
    load_contract,
)
from tools.agent_orchestration_claude_adapter.divergence_log import is_approved, load_divergences
from tools.agent_orchestration_claude_adapter.gate_policy_extractor import extract_gate_policy
from tools.gate_checks.workflow_meta_conformance import extract_meta_phases

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOW_JS_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_DIVERGENCE_LOG_PATH = _REPO_ROOT / "agent-orchestration" / "intentional-divergences.md"


def _gate_triples(gates: list[dict]) -> set[tuple[str, str, tuple[str, ...]]]:
    return {(g["phase"], g["gate_type"], tuple(sorted(g["on_fail_status"]))) for g in gates}


def _diff(live_gates: list[dict], contract_gates: list[dict]):
    live_triples = _gate_triples(live_gates)
    contract_triples = _gate_triples(contract_gates)
    return live_triples - contract_triples, contract_triples - live_triples


def test_gate_policy_conformance_full_match_both_directions():
    live_gates = extract_gate_policy(_WORKFLOW_JS_PATH)
    contract_gates = load_contract(_REPO_ROOT).gate_policy["gates"]

    missing_from_contract, missing_from_live = _diff(live_gates, contract_gates)

    if missing_from_contract or missing_from_live:
        divergences = load_divergences(_DIVERGENCE_LOG_PATH)
        mismatched_phases = {phase for phase, _gate_type, _statuses in missing_from_contract | missing_from_live}
        unapproved = {
            phase for phase in mismatched_phases
            if not is_approved(divergences, axis="gate_policy", value=phase)
        }
        assert not unapproved, (
            f"gate-policy mismatch not covered by a human-approved entry in "
            f"{_DIVERGENCE_LOG_PATH}: missing_from_contract={missing_from_contract}, "
            f"missing_from_live={missing_from_live}, unapproved phases={unapproved}"
        )


def test_gate_policy_extractor_covers_all_12_phases_or_explicitly_excludes_a_gateless_phase():
    live_phases = set(extract_meta_phases(_WORKFLOW_JS_PATH))
    assert len(live_phases) == 12

    gate_policy = load_contract(_REPO_ROOT).gate_policy
    gated_phases = {g["phase"] for g in gate_policy["gates"]}
    gateless_phases = {g["phase"] for g in gate_policy.get("gateless_phases", [])}
    excluded_outcome_phases = {o["phase"] for o in gate_policy.get("excluded_outcomes", [])}

    accounted_for = gated_phases | gateless_phases | excluded_outcome_phases
    unaccounted = live_phases - accounted_for
    assert not unaccounted, (
        f"phase(s) {unaccounted} declared in implement-ticket.js's meta.phases but not represented "
        f"in gate-policy.yaml's gates/gateless_phases/excluded_outcomes — every phase must be "
        f"explicitly gated or explicitly documented as gateless/excluded, never silently missing"
    )


def test_gate_policy_deliberately_introduced_mismatch_fails_without_approval(tmp_path):
    live_gates = extract_gate_policy(_WORKFLOW_JS_PATH)
    contract_gates = [dict(g) for g in load_contract(_REPO_ROOT).gate_policy["gates"]]

    mutated_gates = []
    for gate in contract_gates:
        gate = dict(gate)
        if gate["phase"] == "Review" and gate["gate_type"] == "agent_verdict":
            gate["on_fail_status"] = ["WRONG_STATUS_VALUE"]
        mutated_gates.append(gate)

    missing_from_contract, missing_from_live = _diff(live_gates, mutated_gates)
    assert missing_from_contract or missing_from_live, "mutation did not actually introduce a mismatch"

    unapproved_log = tmp_path / "intentional-divergences-unapproved.md"
    unapproved_log.write_text("# Intentional Divergences\n\nNo entries yet.\n", encoding="utf-8")
    divergences = load_divergences(unapproved_log)
    assert not is_approved(divergences, axis="gate_policy", value="Review"), (
        "an empty divergence log must never suppress a real mismatch"
    )

    approved_log = tmp_path / "intentional-divergences-approved.md"
    approved_log.write_text(
        "\n".join([
            "## gate_policy:Review",
            "Axis: gate_policy",
            "Contract-value: on_fail_status=WRONG_STATUS_VALUE",
            "Live-value: on_fail_status=NEEDS_CHANGES,BLOCKED",
            "Rationale: deliberately-introduced test fixture proving the approval mechanism works.",
            "Approved-by: test-fixture",
            "Approved-date: 2026-09-04",
            "Status: RATIFIED",
            "",
        ]),
        encoding="utf-8",
    )
    divergences = load_divergences(approved_log)
    assert is_approved(divergences, axis="gate_policy", value="Review"), (
        "a fully-formed RATIFIED entry must suppress the matching mismatch"
    )


def test_gate_policy_does_not_duplicate_static_check_internal_logic():
    gate_policy = load_contract(_REPO_ROOT).gate_policy
    for entry in gate_policy["gates"]:
        allowed_keys = set(_REQUIRED_GATE_ENTRY_KEYS) | set(_GATE_TYPE_EXTRA_KEYS[entry["gate_type"]])
        extra_keys = set(entry.keys()) - allowed_keys
        assert not extra_keys, (
            f"gate entry {entry!r} carries key(s) {extra_keys} outside the documented schema — "
            f"this schema must never grow a per-DoD-condition breakdown (e.g. "
            f"done_checker_static.py's ~13 named sub-conditions); it records only which "
            f"module/function backs a gate and which terminal-status value(s) result"
        )
