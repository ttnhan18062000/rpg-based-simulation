"""In-process Codex shadow-outcome derivation for tools/agent_codex_runtime_shadow/.

`derive_codex_shadow_outcome()` is the in-process functional replacement for
`agent_replay_codex.invoker.run_codex_replay()`: it operates entirely on an already-loaded
`FixtureEnvelope` and NEVER spawns a subprocess or a real `codex exec` invocation. It walks
`fixture.phases` in the same iteration shape as `tools.agent_replay.runner.replay_slice()` but
never imports or calls that function — this must stay a structurally independent, non-Claude-side
derivation so shadow_comparison.py's comparison against the real `replay_slice()` output is
meaningful, not circular.

`final_status`/`gate_result` vocabulary is normalized the same way
`tools.agent_replay.runner.replay_slice()` normalizes verdicts (`"ok"` when Review's verdict is
`APPROVED`, else the raw verdict string) — re-implemented here, not imported, since
`replay_slice()` has no standalone normalization function to import. This avoids reintroducing the
vocabulary bug `tickets/done/TCK-20260721-CODEX-REPLAY-PARITY.md` Implementation Notes Step 11
already found and fixed once in `shadow_mode.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.agent_replay.fixture_envelope import FixtureEnvelope

from . import gate_validation, matrix, phase_order, required_artifacts


@dataclass(frozen=True)
class CodexShadowOutcome:
    final_status: str
    phases_completed: list[str]
    gate_result: str
    artifacts_verified: dict[str, list[str]]


def derive_codex_shadow_outcome(fixture: FixtureEnvelope, artifacts_dir: Path) -> CodexShadowOutcome:
    supported_matrix = matrix.load_supported_matrix()
    phase_names = [p.phase for p in fixture.phases]

    matrix.validate_phase_names(phase_names, supported_matrix)
    matrix.validate_contract_version(supported_matrix)
    matrix.validate_tier(fixture.source.get("tier"), supported_matrix)
    phase_order.validate_phase_order(phase_names, supported_matrix)

    phases_completed: list[str] = []
    artifacts_verified: dict[str, list[str]] = {}
    gate_result = ""  # only the Review phase ever sets this; absent Review leaves it unset

    for entry in fixture.phases:
        gate_validation.validate_required_gate(entry)
        artifacts_verified[entry.phase] = required_artifacts.check_required_artifacts(
            entry.phase, fixture.source["ticket_id"], artifacts_dir
        )
        if entry.phase == "Review":
            verdict = entry.output.get("verdict")
            gate_result = "ok" if verdict == "APPROVED" else verdict
        phases_completed.append(entry.phase)

    return CodexShadowOutcome(
        final_status=gate_result,
        phases_completed=phases_completed,
        gate_result=gate_result,
        artifacts_verified=artifacts_verified,
    )
