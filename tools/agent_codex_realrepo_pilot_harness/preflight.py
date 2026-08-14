"""No-write, fail-closed admission for an injected scratch repository."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from tools.agent_codex_pilot_guardrails.enabled_surface import assert_enabled_surface_subset
from tools.agent_codex_pilot_guardrails.pilot_manifest import PilotRequest, load_pilot_request
from tools.agent_codex_pilot_guardrails.ticket_selection import assert_no_concurrent_claim
from tools.agent_codex_posttool_adapter.identity import validate_identity

from .errors import RootAdmissionRefused
from .policy import ExpectedWritePolicy, load_policy_file
from .proofs import capture_policy_baseline, tree_digest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PilotHarnessContext:
    repo_root: Path
    ticket_id: str
    execution_id: str
    candidate_path: str
    request_path: str
    policy_path: str
    enabled_hook_events: frozenset[str]
    enabled_writer_names: frozenset[str]
    concurrent_runs: tuple[dict, ...]


@dataclass(frozen=True)
class PreflightResult:
    context: PilotHarnessContext
    root: Path
    request: PilotRequest
    policy: ExpectedWritePolicy
    baseline_tree: dict[str, bytes]
    baseline_digest: str


@dataclass(frozen=True)
class _CapturedPreflightEvidence:
    """Validated evidence shared by ordinary and future live preflight paths."""

    request: PilotRequest
    policy: ExpectedWritePolicy
    baseline_tree: dict[str, bytes]
    baseline_digest: str


def _contained(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise RootAdmissionRefused("derived path must be a safe relative path")
    path = Path(relative)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise RootAdmissionRefused("derived path must be a safe relative path")
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise RootAdmissionRefused("derived path escapes injected root")
    return resolved


def _admit_ordinary_root(value: Path | str) -> Path:
    root = Path(value).resolve()
    project = _PROJECT_ROOT.resolve()
    if root == project or project in root.parents:
        raise RootAdmissionRefused("ordinary harness admission refuses project root or child")
    if not root.is_dir():
        raise RootAdmissionRefused("injected scratch root must exist")
    return root


def _capture_preflight_evidence(context: PilotHarnessContext, root: Path) -> _CapturedPreflightEvidence:
    """Capture common immutable evidence after a caller has admitted its root."""
    # Identity has no filesystem I/O and must precede ticket-derived paths.
    validate_identity("codex", context.execution_id, context.ticket_id)
    candidate = _contained(root, context.candidate_path)
    request_path = _contained(root, context.request_path)
    policy_path = _contained(root, context.policy_path)
    # Only now is any derived path opened.
    if not candidate.is_file():
        raise RootAdmissionRefused("candidate ticket is missing")
    request = load_pilot_request(request_path)
    if request.ticket_id != context.ticket_id:
        raise RootAdmissionRefused("pilot request ticket does not match candidate")
    assert_enabled_surface_subset(context.enabled_hook_events, context.enabled_writer_names)
    assert_no_concurrent_claim(context.ticket_id, list(context.concurrent_runs))
    policy = load_policy_file(policy_path, context.ticket_id)
    baseline = capture_policy_baseline(root, policy_path)
    digest = tree_digest(baseline)
    if policy.request_sha256 != hashlib.sha256(request_path.read_bytes()).hexdigest():
        raise RootAdmissionRefused("policy request hash does not match captured request")
    if policy.baseline_sha256 != digest:
        raise RootAdmissionRefused("policy baseline hash does not match captured baseline")
    return _CapturedPreflightEvidence(request, policy, baseline, digest)


def ordinary_preflight(context: PilotHarnessContext | Path | str, ticket_id: str | None = None) -> PreflightResult:
    """Capture all immutable evidence before any claim, config, or invoker operation.

    The compatibility Path form is intentionally refusal-only; normal callers use
    ``PilotHarnessContext`` so all derived paths are validated together.
    """
    if not isinstance(context, PilotHarnessContext):
        _admit_ordinary_root(context)
        raise RootAdmissionRefused("a complete immutable pilot context is required")
    evidence = _capture_preflight_evidence(context, _admit_ordinary_root(context.repo_root))
    return PreflightResult(
        context,
        Path(context.repo_root).resolve(),
        evidence.request,
        evidence.policy,
        evidence.baseline_tree,
        evidence.baseline_digest,
    )


def load_contained_policy(scratch_root: Path | str, policy_path: Path | str, candidate_ticket_id: str) -> ExpectedWritePolicy:
    root = _admit_ordinary_root(scratch_root)
    supplied = Path(policy_path)
    # Convert to relative before any policy open; this retains containment proof.
    try:
        relative = supplied.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise RootAdmissionRefused("policy path escapes injected scratch root") from exc
    return load_policy_file(_contained(root, relative), candidate_ticket_id)
