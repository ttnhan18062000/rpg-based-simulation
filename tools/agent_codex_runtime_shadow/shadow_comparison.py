"""Shadow comparison against the canonical Claude-side runner, with a RATIFIED-divergence escape
hatch, for tools/agent_codex_runtime_shadow/.

`ReplayOutcome` (tools/agent_replay/runner.py) stays a 2-field dataclass — `ShadowComparisonResult`
is the new, additive comparison type this ticket introduces rather than extending that shared
type. Compares on exactly the 4 axes `agent-orchestration/intentional-divergences.md`'s own
`## Entry Format` section documents (`terminal_status`, `phase_order`, `gate_policy`,
`artifact_requirements`) — not the predecessor's undocumented `"codex_parity"` catch-all.

`run_shadow_comparison()` is the single public top-level entry point: it makes the one and only
import of `tools.agent_replay.runner.replay_slice()` (the canonical Claude-side ground truth) in
this whole package — read-only call, no modification.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.agent_orchestration_claude_adapter.divergence_log import Divergence, is_approved, load_divergences
from tools.agent_replay.fixture_envelope import FixtureEnvelope, load_fixture
from tools.agent_replay.runner import ReplayOutcome, replay_slice

from . import required_artifacts, shadow_runner
from .errors import ShadowMismatchError
from .shadow_runner import CodexShadowOutcome

_SUPPORTED_AXES = {"terminal_status", "phase_order", "gate_policy", "artifact_requirements"}


@dataclass(frozen=True)
class ShadowComparisonResult:
    ticket_id: str
    phase_order_match: bool
    terminal_status_match: bool
    gate_policy_match: bool
    artifact_requirements_match: bool
    suppressed_axes: list[str]


def _axis_is_approved(divergences: list[Divergence], axis: str, ticket_id: str) -> bool:
    if axis not in _SUPPORTED_AXES:
        raise ValueError(f"unsupported divergence axis {axis!r}: must be one of {_SUPPORTED_AXES}")
    return is_approved(divergences, axis, ticket_id)


def compare_to_canonical(
    fixture: FixtureEnvelope,
    claude_outcome: ReplayOutcome,
    codex_outcome: CodexShadowOutcome,
    claude_artifacts_verified: dict[str, list[str]],
    divergences_path: Path,
) -> ShadowComparisonResult:
    ticket_id = fixture.source["ticket_id"]

    raw_matches = {
        "phase_order": claude_outcome.phases_completed == codex_outcome.phases_completed,
        "terminal_status": claude_outcome.final_status == codex_outcome.final_status,
        "gate_policy": claude_outcome.final_status == codex_outcome.gate_result,
        "artifact_requirements": claude_artifacts_verified == codex_outcome.artifacts_verified,
    }

    divergences = load_divergences(divergences_path)
    suppressed_axes: list[str] = []
    hard_failures: list[str] = []
    for axis, matched in raw_matches.items():
        if matched:
            continue
        if _axis_is_approved(divergences, axis, ticket_id):
            suppressed_axes.append(axis)
        else:
            hard_failures.append(axis)

    if hard_failures:
        raise ShadowMismatchError(
            f"{ticket_id}: shadow comparison mismatch on axis/axes {hard_failures!r} with no "
            "covering RATIFIED divergence"
        )

    return ShadowComparisonResult(
        ticket_id=ticket_id,
        phase_order_match=raw_matches["phase_order"] or "phase_order" in suppressed_axes,
        terminal_status_match=raw_matches["terminal_status"] or "terminal_status" in suppressed_axes,
        gate_policy_match=raw_matches["gate_policy"] or "gate_policy" in suppressed_axes,
        artifact_requirements_match=(
            raw_matches["artifact_requirements"] or "artifact_requirements" in suppressed_axes
        ),
        suppressed_axes=suppressed_axes,
    )


def run_shadow_comparison(
    fixture_path: Path, artifacts_dir: Path, divergences_path: Path
) -> ShadowComparisonResult:
    fixture = load_fixture(fixture_path)
    claude_outcome = replay_slice(fixture)

    ticket_id = fixture.source["ticket_id"]
    # source.stored_artifacts_dir already ends in "<ticket_id>/" — its parent is the root
    # required_artifacts.check_required_artifacts() expects, since that function itself appends
    # ticket_id when joining with the required filename.
    stored_artifacts_root = Path(fixture.source["stored_artifacts_dir"]).parent
    claude_artifacts_verified: dict[str, list[str]] = {
        phase: required_artifacts.check_required_artifacts(phase, ticket_id, stored_artifacts_root)
        for phase in claude_outcome.phases_completed
    }

    codex_outcome = shadow_runner.derive_codex_shadow_outcome(fixture, artifacts_dir)

    return compare_to_canonical(
        fixture, claude_outcome, codex_outcome, claude_artifacts_verified, divergences_path
    )
