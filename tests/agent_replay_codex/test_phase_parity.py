"""Phase-parity test: Python-runner output vs. Codex-adapter output on the same fixture
(TCK-20260721-CODEX-REPLAY-PARITY, Step 8, AC #4). Uses the same session-scoped
`real_codex_replay` fixture from conftest.py — no second real invocation.
"""
from __future__ import annotations

from pathlib import Path

from tools.agent_orchestration_claude_adapter.divergence_log import is_approved, load_divergences
from tools.agent_replay.fixture_envelope import load_fixture
from tools.agent_replay.runner import replay_slice

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)
_DIVERGENCE_LOG_PATH = _REPO_ROOT / "agent-orchestration" / "intentional-divergences.md"


def test_codex_execution_path_matches_python_runner_output(real_codex_replay):
    python_outcome = replay_slice(load_fixture(_REAL_FIXTURE_PATH))
    codex_outcome = real_codex_replay["outcome"]

    if (
        python_outcome.final_status != codex_outcome.final_status
        or python_outcome.phases_completed != codex_outcome.phases_completed
    ):
        divergences = load_divergences(_DIVERGENCE_LOG_PATH)
        assert is_approved(divergences, "codex_parity", "TCK-20260721-ORCHESTRATION-CONTRACT-ADR"), (
            f"Codex-side execution ({codex_outcome}) diverges from Python runner ({python_outcome}) "
            "with no matching RATIFIED entry in agent-orchestration/intentional-divergences.md"
        )
    else:
        assert python_outcome.final_status == codex_outcome.final_status
        assert python_outcome.phases_completed == codex_outcome.phases_completed
