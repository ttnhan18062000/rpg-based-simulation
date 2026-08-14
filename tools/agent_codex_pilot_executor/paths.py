"""Validated, contained paths below a caller-injected scratch root."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.agent_codex_posttool_adapter.identity import validate_identity

from .errors import ScratchContainmentError

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REAL_MONITORING = _REPO_ROOT / "agent-monitoring"


@dataclass(frozen=True)
class ScratchPaths:
    root: Path
    request_dir: Path
    claims_dir: Path
    monitoring_dir: Path
    request_path: Path
    claim_path: Path
    lock_path: Path


def _contained(path: Path, parent: Path) -> Path:
    resolved_parent = parent.resolve()
    resolved = path.resolve()
    if resolved != resolved_parent and resolved_parent not in resolved.parents:
        raise ScratchContainmentError(f"path escapes scratch parent: {resolved}")
    return resolved


def resolve_scratch_paths(*, scratch_root: Path, ticket_id: str, execution_id: str) -> ScratchPaths:
    """Validate identity before constructing ticket-derived paths or doing I/O."""
    # validate_identity is pure and is deliberately first: no ticket-derived Path
    # expression precedes it.
    validate_identity("codex", execution_id, ticket_id)

    root = scratch_root.resolve()
    repo = _REPO_ROOT.resolve()
    monitoring = _REAL_MONITORING.resolve()
    if root == repo or root == monitoring or repo in root.parents or monitoring in root.parents:
        raise ScratchContainmentError(f"scratch root must be outside repository: {root}")

    request_dir = _contained(root / "pilot_requests", root)
    claims_dir = _contained(root / "claims", root)
    monitoring_dir = _contained(root / "agent-monitoring", root)
    request_path = _contained(request_dir / f"{ticket_id}.yaml", request_dir)
    claim_path = _contained(claims_dir / f"{ticket_id}.json", claims_dir)
    lock_path = _contained(claims_dir / f"{ticket_id}.json.lock", claims_dir)
    return ScratchPaths(
        root=root,
        request_dir=request_dir,
        claims_dir=claims_dir,
        monitoring_dir=monitoring_dir,
        request_path=request_path,
        claim_path=claim_path,
        lock_path=lock_path,
    )
