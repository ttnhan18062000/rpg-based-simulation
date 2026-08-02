"""Required-gate validation for tools/agent_codex_runtime_shadow/.

Standalone pre-check, not a call into or modification of
tools.agent_replay.runner.replay_slice()'s own Review-verdict branch. Only Review carries a
required-gate concept in this ticket's supported slice, matching replay_slice()'s own
Review-only gate branch — every other phase is a no-op here.
"""
from __future__ import annotations

from tools.agent_replay.fixture_envelope import PhaseEntry

from .errors import RequiredGateMissingError


def validate_required_gate(phase_entry: PhaseEntry) -> None:
    if phase_entry.phase != "Review":
        return
    if not phase_entry.output.get("verdict"):
        raise RequiredGateMissingError(
            "Review phase entry is missing required output.verdict"
        )
