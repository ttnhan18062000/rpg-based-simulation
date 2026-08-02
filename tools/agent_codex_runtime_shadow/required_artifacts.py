"""Required-artifact validation for tools/agent_codex_runtime_shadow/.

Generic, path-parameterized artifact-existence checker (mirrors
tools/agent_replay_codex/containment.py's `repo_root`-parameterization precedent) — does not
hardcode which root (`staging_artifacts/` vs. `stored_artifacts/`) is used; callers pass
`artifacts_dir` explicitly.

The scratch/shadow convention callers should default to is `<repo_root>/staging_artifacts/` (per
CLAUDE.md's live in-flight artifact convention). A shadow-comparison-against-a-DONE-ticket's-
fixture caller instead passes that fixture's own `source["stored_artifacts_dir"]`. Both are
legitimate uses of the same function, not a special case.

Additive and external to tools/agent_replay/fixture_envelope.py's FixtureEnvelope/PhaseEntry
schema — no artifact-path field is added there, per the anti-drift hazard against extending the
fixture envelope format.
"""
from __future__ import annotations

from pathlib import Path

from .errors import RequiredArtifactMissingError

REQUIRED_ARTIFACTS_BY_PHASE: dict[str, list[str]] = {
    "Investigate": ["investigation.md", "test_plan.md"],
    "Plan": ["plan.md"],
}


def check_required_artifacts(phase: str, ticket_id: str, artifacts_dir: Path) -> list[str]:
    """Returns the list of required filenames confirmed present for `phase`, in
    REQUIRED_ARTIFACTS_BY_PHASE[phase] order. No-op (returns []) for a phase with no required
    artifact entry. Raises RequiredArtifactMissingError naming the first missing filename if any
    required file is absent."""
    required = REQUIRED_ARTIFACTS_BY_PHASE.get(phase, [])
    found: list[str] = []
    for filename in required:
        if not (Path(artifacts_dir) / ticket_id / filename).exists():
            raise RequiredArtifactMissingError(
                f"phase {phase!r}: required artifact {filename!r} not found under "
                f"{Path(artifacts_dir) / ticket_id}"
            )
        found.append(filename)
    return found
