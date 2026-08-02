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


def validate_contract_version(declared_version: int, matrix: SupportedMatrix) -> None:
    if declared_version != matrix.workflow_version:
        raise ContractVersionMismatchError(
            f"declared workflow_version {declared_version!r} does not match the real "
            f"implement-ticket.yaml's workflow_version {matrix.workflow_version!r}"
        )
