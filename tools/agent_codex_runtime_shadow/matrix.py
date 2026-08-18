"""Phase/tier support matrix for tools/agent_codex_runtime_shadow/.

Reads `workflow_version` from the real `agent-orchestration/workflows/implement-ticket.yaml`
(read-only — never written by this package) but does NOT auto-derive "the smallest useful slice"
of supported phases/tiers from that file's own `tiers`/`condition` fields. Per
investigation.md's Resolved Open Question 1, the supported slice is hardcoded to this ticket's own
explicit decision: `tier=standard` only, `phases=[Scope, Investigate, Plan, Review]` only — the
exact slice the one real fixture (tests/fixtures/agent_replay/) and canonical runner
(tools/agent_replay/runner.py) cover. Every other tier/phase is a deterministic, typed rejection.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .errors import ContractVersionMismatchError, UnsupportedPhaseError, UnsupportedTierError

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_WORKFLOW_YAML_PATH = _REPO_ROOT / "agent-orchestration" / "workflows" / "implement-ticket.yaml"

_SUPPORTED_TIER = "standard"
_SUPPORTED_PHASES = ["Scope", "Investigate", "Plan", "Review"]

# The implement-ticket.yaml workflow_version this package's Scope/Investigate/Plan/Review
# phase/gate logic (matrix.py, shadow_runner.py, phase_order.py, gate_validation.py,
# required_artifacts.py) was last manually reviewed against. Hardcoded-by-design, same spirit as
# _SUPPORTED_TIER/_SUPPORTED_PHASES above -- bump only after re-reviewing this package's own
# assumptions against a real implement-ticket.yaml change, never automatically.
#
# TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION: this used to be
# conflated with an individual FixtureEnvelope.version (the replay-fixture-ENVELOPE schema
# version, a completely different, independently-owned concept -- see
# docs/ai/replay_fixture_spec.md -- pinned at 1 by TCK-20260721-CODEX-REPLAY-PROOF and asserted
# so by tests/agent_replay/test_fixture_envelope.py). That conflation broke the moment
# workflow_version was legitimately bumped for reasons unrelated to this package (continuation_policy,
# TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY) -- every fixture's own frozen envelope version
# would need re-stamping forever just to keep pace with orchestrator changes this package's own
# supported phase/gate slice never actually needs to react to. A contract-version check answers
# "is THIS PACKAGE's own hardcoded phase/gate contract still what the live orchestrator expects,"
# which has nothing to do with when any individual fixture was captured.
_VERIFIED_AGAINST_WORKFLOW_VERSION = 2


@dataclass(frozen=True)
class SupportedMatrix:
    tier: str
    phases: list[str]
    workflow_version: int


def load_supported_matrix(workflow_yaml_path: Path = _DEFAULT_WORKFLOW_YAML_PATH) -> SupportedMatrix:
    """Load the real implement-ticket.yaml's `workflow_version` and pair it with this ticket's
    hardcoded supported tier/phase slice."""
    raw = yaml.safe_load(Path(workflow_yaml_path).read_text(encoding="utf-8"))
    workflow_version = raw.get("workflow_version") if isinstance(raw, dict) else None
    if not isinstance(workflow_version, int):
        raise ContractVersionMismatchError(
            f"{workflow_yaml_path}: missing or non-int top-level field 'workflow_version'"
        )
    return SupportedMatrix(
        tier=_SUPPORTED_TIER,
        phases=list(_SUPPORTED_PHASES),
        workflow_version=workflow_version,
    )


def validate_tier(tier: str, matrix: SupportedMatrix) -> None:
    if tier != matrix.tier:
        raise UnsupportedTierError(
            f"unsupported tier {tier!r}: only {matrix.tier!r} is supported by this shadow runtime"
        )


def validate_phase_names(phase_names: list[str], matrix: SupportedMatrix) -> None:
    """Whole-input rejection: raises on the first offending phase name before any phase-by-phase
    processing proceeds — never a partial pass."""
    for name in phase_names:
        if name not in matrix.phases:
            raise UnsupportedPhaseError(
                f"unsupported phase {name!r}: only {matrix.phases} are supported by this shadow "
                "runtime"
            )


def validate_contract_version(matrix: SupportedMatrix) -> None:
    """Not a per-fixture check -- validates that THIS PACKAGE's own hardcoded phase/gate
    assumptions (_VERIFIED_AGAINST_WORKFLOW_VERSION) still match the live
    implement-ticket.yaml's real workflow_version. See _VERIFIED_AGAINST_WORKFLOW_VERSION's own
    docstring for why this is deliberately decoupled from any individual FixtureEnvelope.version."""
    if matrix.workflow_version != _VERIFIED_AGAINST_WORKFLOW_VERSION:
        raise ContractVersionMismatchError(
            f"this package was last verified against workflow_version "
            f"{_VERIFIED_AGAINST_WORKFLOW_VERSION!r}, but the real implement-ticket.yaml's "
            f"workflow_version is now {matrix.workflow_version!r} -- re-review "
            "tools/agent_codex_runtime_shadow/'s phase/gate assumptions against the real "
            "orchestrator change before bumping _VERIFIED_AGAINST_WORKFLOW_VERSION"
        )
