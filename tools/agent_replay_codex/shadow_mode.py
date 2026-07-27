"""Shadow-mode comparison (TCK-20260721-CODEX-REPLAY-PARITY, Step 11, AC #7).

Claude's side is read directly from the fixture's own embedded phases/source data — already
real, already derived from the done ticket + real agent-monitoring/events.jsonl rows (see the
fixture file's own header comment) — never a new live query, never a write anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass

from tools.agent_replay.fixture_envelope import FixtureEnvelope
from tools.agent_replay_codex.invoker import CodexReplayOutcome


@dataclass(frozen=True)
class ShadowModeComparison:
    ticket_id: str
    claude_final_status: str
    claude_phases_completed: list[str]
    claude_gate_result: str          # Review phase's real recorded verdict, from the fixture
    claude_artifact_refs: list[str]  # fixture's source.stored_artifacts_dir
    codex_final_status: str
    codex_phases_completed: list[str]
    codex_gate_result: str
    match: bool


def compare_claude_and_codex(
    fixture: FixtureEnvelope, codex_outcome: CodexReplayOutcome
) -> ShadowModeComparison:
    review_phase = next(p for p in fixture.phases if p.phase == "Review")
    review_verdict = review_phase.output["verdict"]
    # Normalized into the same vocabulary tools.agent_replay.runner.replay_slice() produces for
    # final_status: "ok" when the Review gate passed (verdict == APPROVED), else the raw verdict
    # string — both sides of this comparison must speak the same vocabulary for `match` to be
    # meaningful, since replay_slice() never returns the literal string "APPROVED" itself.
    claude_gate_result = "ok" if review_verdict == "APPROVED" else review_verdict
    claude_phases_completed = [p.phase for p in fixture.phases]
    claude_final_status = fixture.source.get("final_status", claude_gate_result)
    claude_artifact_refs = [fixture.source["stored_artifacts_dir"]]

    codex_gate_result = codex_outcome.final_status

    match = (
        claude_phases_completed == codex_outcome.phases_completed
        and claude_gate_result == codex_gate_result
    )

    return ShadowModeComparison(
        ticket_id=fixture.source["ticket_id"],
        claude_final_status=claude_final_status,
        claude_phases_completed=claude_phases_completed,
        claude_gate_result=claude_gate_result,
        claude_artifact_refs=claude_artifact_refs,
        codex_final_status=codex_outcome.final_status,
        codex_phases_completed=codex_outcome.phases_completed,
        codex_gate_result=codex_gate_result,
        match=match,
    )
