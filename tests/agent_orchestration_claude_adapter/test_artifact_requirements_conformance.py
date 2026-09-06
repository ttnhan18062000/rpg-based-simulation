"""Artifact-requirements conformance test: LIVE `tools/gate_checks/done_checker_static.py`
extraction vs. `agent-orchestration/contract.yaml`'s `artifact_requirements` field
(TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST, AC #2).

Diffed live-code -> contract (never the reverse), matching this ticket's own Scope instruction and
the 2 existing Claude-adapter conformance tests' direction. Any mismatch is checked against
`divergence_log.is_approved()` (axis="artifact_requirements", value="required_files") before
hard-failing.
"""
from __future__ import annotations

from pathlib import Path

from tools.agent_orchestration.loader import load_contract
from tools.agent_orchestration_claude_adapter.artifact_requirements_extractor import (
    extract_live_artifact_requirements,
)
from tools.agent_orchestration_claude_adapter.divergence_log import is_approved, load_divergences

_REPO_ROOT = Path(__file__).parent.parent.parent
_DIVERGENCE_LOG_PATH = _REPO_ROOT / "agent-orchestration" / "intentional-divergences.md"


def test_artifact_requirements_conformance_full_match():
    live = extract_live_artifact_requirements(_REPO_ROOT)
    contract = load_contract(_REPO_ROOT).artifact_requirements

    if live == contract:
        return

    divergences = load_divergences(_DIVERGENCE_LOG_PATH)
    assert is_approved(divergences, axis="artifact_requirements", value="required_files"), (
        f"artifact_requirements mismatch not covered by a human-approved entry in "
        f"{_DIVERGENCE_LOG_PATH}: live={live!r} vs contract={contract!r}"
    )


def test_artifact_requirements_deliberately_introduced_mismatch_fails_without_approval(tmp_path):
    live = extract_live_artifact_requirements(_REPO_ROOT)
    mutated_contract = {
        "required_files": [f for f in live["required_files"] if f != "investigation.md"],
        "exempt_tier": live["exempt_tier"],
    }
    assert mutated_contract != live, "mutation did not actually introduce a mismatch"

    unapproved_log = tmp_path / "intentional-divergences-unapproved.md"
    unapproved_log.write_text("# Intentional Divergences\n\nNo entries yet.\n", encoding="utf-8")
    divergences = load_divergences(unapproved_log)
    assert not is_approved(divergences, axis="artifact_requirements", value="required_files"), (
        "an empty divergence log must never suppress a real mismatch"
    )

    approved_log = tmp_path / "intentional-divergences-approved.md"
    approved_log.write_text(
        "\n".join([
            "## artifact_requirements:required_files",
            "Axis: artifact_requirements",
            "Contract-value: [plan.md, test_plan.md]",
            "Live-value: [plan.md, investigation.md, test_plan.md]",
            "Rationale: deliberately-introduced test fixture proving the approval mechanism works.",
            "Approved-by: test-fixture",
            "Approved-date: 2026-09-04",
            "Status: RATIFIED",
            "",
        ]),
        encoding="utf-8",
    )
    divergences = load_divergences(approved_log)
    assert is_approved(divergences, axis="artifact_requirements", value="required_files"), (
        "a fully-formed RATIFIED entry must suppress the matching mismatch"
    )
