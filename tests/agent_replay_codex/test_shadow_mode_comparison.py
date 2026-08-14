"""Shadow-mode comparison test (TCK-20260721-CODEX-REPLAY-PARITY, Step 11, AC #7). Uses the
Step 7 shared `real_codex_replay` fixture — no third real invocation.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from tools.agent_orchestration_claude_adapter.divergence_log import is_approved, load_divergences
from tools.agent_replay.fixture_envelope import load_fixture
from tools.agent_replay_codex.shadow_mode import compare_claude_and_codex

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)
_DIVERGENCE_LOG_PATH = _REPO_ROOT / "agent-orchestration" / "intentional-divergences.md"
_WATCHED_PATHSPECS = ["tickets/", "agent-orchestration/", ".claude/"]


def _porcelain() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--", *_WATCHED_PATHSPECS],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_n1_comparison_against_existing_fixture(real_codex_replay):
    pre = _porcelain()

    fixture = load_fixture(_REAL_FIXTURE_PATH)
    comparison = compare_claude_and_codex(fixture, real_codex_replay["outcome"])

    post = _porcelain()
    assert pre == post, (
        "compare_claude_and_codex is a pure in-memory function — it must never write to "
        "tickets/, agent-orchestration/, or .claude/"
    )

    if not comparison.match:
        divergences = load_divergences(_DIVERGENCE_LOG_PATH)
        assert is_approved(divergences, "codex_parity", "TCK-20260721-ORCHESTRATION-CONTRACT-ADR"), (
            f"shadow-mode comparison mismatch with no matching RATIFIED divergence entry: "
            f"{comparison}"
        )
    else:
        assert comparison.match is True
