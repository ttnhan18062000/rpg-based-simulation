"""Private real-root preflight capability for a future reviewed transport."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.agent_codex_pilot_guardrails.pilot_manifest import PilotRequest

from .errors import RootAdmissionRefused
from .policy import ExpectedWritePolicy
from .preflight import PilotHarnessContext, _capture_preflight_evidence


_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class LivePreflightResult:
    """Immutable real-root evidence; constructed only by the private factory."""

    context: PilotHarnessContext
    root: Path
    request: PilotRequest
    policy: ExpectedWritePolicy
    baseline_tree: dict[str, bytes]
    baseline_digest: str


def _create_live_preflight(context: PilotHarnessContext) -> LivePreflightResult:
    """Sanctioned real-root factory; future pilot code must call this only when authorized."""
    root = Path(context.repo_root).resolve()
    if root != _PROJECT_ROOT.resolve() or not root.is_dir():
        raise RootAdmissionRefused("live preflight requires the canonical project root")
    evidence = _capture_preflight_evidence(context, root)
    return LivePreflightResult(
        context,
        root,
        evidence.request,
        evidence.policy,
        evidence.baseline_tree,
        evidence.baseline_digest,
    )
