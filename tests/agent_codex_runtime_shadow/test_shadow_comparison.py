"""Tests for tools/agent_codex_runtime_shadow/shadow_comparison.py
(TCK-20260730-CODEX-RUNTIME-SHADOW, Step 7)."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_codex_runtime_shadow.errors import ShadowMismatchError
from tools.agent_codex_runtime_shadow.shadow_comparison import compare_to_canonical, run_shadow_comparison
from tools.agent_codex_runtime_shadow.shadow_runner import CodexShadowOutcome
from tools.agent_replay.fixture_envelope import FixtureEnvelope, load_fixture
from tools.agent_replay.runner import ReplayOutcome, replay_slice

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)
_EMPTY_DIVERGENCE_LOG = "# no entries\n"


def _write_scratch_artifacts(tmp_path: Path, ticket_id: str) -> Path:
    artifacts_dir = tmp_path / "staging_artifacts"
    ticket_dir = artifacts_dir / ticket_id
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "investigation.md").write_text("x", encoding="utf-8")
    (ticket_dir / "test_plan.md").write_text("x", encoding="utf-8")
    (ticket_dir / "plan.md").write_text("x", encoding="utf-8")
    return artifacts_dir


def test_shadow_comparison_matches_canonical_fixture(tmp_path):
    artifacts_dir = _write_scratch_artifacts(tmp_path, "TCK-20260721-ORCHESTRATION-CONTRACT-ADR")
    divergences_path = tmp_path / "intentional-divergences.md"
    divergences_path.write_text(_EMPTY_DIVERGENCE_LOG, encoding="utf-8")

    result = run_shadow_comparison(_REAL_FIXTURE_PATH, artifacts_dir, divergences_path)

    assert result.phase_order_match is True
    assert result.terminal_status_match is True
    assert result.gate_policy_match is True
    assert result.artifact_requirements_match is True
    assert result.suppressed_axes == []


def test_shadow_comparison_match_is_false_when_artifacts_differ_but_everything_else_agrees(tmp_path):
    fixture = load_fixture(_REAL_FIXTURE_PATH)
    claude_outcome = replay_slice(fixture)

    codex_outcome = CodexShadowOutcome(
        final_status=claude_outcome.final_status,
        phases_completed=list(claude_outcome.phases_completed),
        gate_result=claude_outcome.final_status,
        artifacts_verified={"Investigate": ["investigation.md"], "Plan": ["plan.md"]},
    )
    claude_artifacts_verified = {
        "Investigate": ["investigation.md", "test_plan.md"],
        "Plan": ["plan.md"],
    }

    divergences_path = tmp_path / "intentional-divergences.md"
    divergences_path.write_text(_EMPTY_DIVERGENCE_LOG, encoding="utf-8")

    with pytest.raises(ShadowMismatchError):
        compare_to_canonical(fixture, claude_outcome, codex_outcome, claude_artifacts_verified, divergences_path)


def _synthetic_fixture(ticket_id: str) -> FixtureEnvelope:
    return FixtureEnvelope(version=1, source={"ticket_id": ticket_id}, phases=[])


def test_shadow_comparison_mismatch_without_ratified_divergence_fails(tmp_path):
    fixture = _synthetic_fixture("FAKE-TICKET")
    claude_outcome = ReplayOutcome(final_status="ok", phases_completed=["Scope", "Investigate"])
    codex_outcome = CodexShadowOutcome(
        final_status="ok",
        phases_completed=["Scope"],
        gate_result="ok",
        artifacts_verified={},
    )

    divergences_path = tmp_path / "intentional-divergences.md"
    divergences_path.write_text(_EMPTY_DIVERGENCE_LOG, encoding="utf-8")

    with pytest.raises(ShadowMismatchError):
        compare_to_canonical(fixture, claude_outcome, codex_outcome, {}, divergences_path)


def test_shadow_comparison_mismatch_with_ratified_divergence_passes(tmp_path):
    fixture = _synthetic_fixture("FAKE-TICKET")
    claude_outcome = ReplayOutcome(final_status="ok", phases_completed=["Scope", "Investigate"])
    codex_outcome = CodexShadowOutcome(
        final_status="ok",
        phases_completed=["Scope"],
        gate_result="ok",
        artifacts_verified={},
    )

    divergences_path = tmp_path / "intentional-divergences.md"
    divergences_path.write_text(
        """\
## phase_order:FAKE-TICKET
Axis: phase_order
Contract-value: phases_completed=[Scope, Investigate]
Live-value: phases_completed=[Scope]
Rationale: synthetic test entry
Approved-by: test-operator
Approved-date: 2026-07-30
Status: RATIFIED
""",
        encoding="utf-8",
    )

    result = compare_to_canonical(fixture, claude_outcome, codex_outcome, {}, divergences_path)

    assert result.phase_order_match is True
    assert result.suppressed_axes == ["phase_order"]
