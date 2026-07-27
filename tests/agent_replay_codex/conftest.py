"""Session-scoped shared real-Codex-invocation fixture (TCK-20260721-CODEX-REPLAY-PARITY, Step 7).

Every real `codex exec` call costs real account usage — one real invocation is shared across
every test that needs it, not one per test. Not `autouse=True`: only tests that explicitly
request `real_codex_replay` trigger a real invocation, so `pytest tests/agent_replay_codex/ -v`
without consent set skips cleanly rather than gating every test in the directory on a real API
call.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from tools.agent_replay_codex.codex_config_guard import snapshot_config_bytes
from tools.agent_replay_codex.consent_gate import CONSENT_ENV_VAR
from tools.agent_replay_codex.containment import capture_snapshot
from tools.agent_replay_codex.invoker import run_codex_replay

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)


@pytest.fixture(scope="session")
def real_codex_replay(request):
    if shutil.which("codex") is None:
        pytest.skip("codex CLI not on PATH")
    if os.environ.get(CONSENT_ENV_VAR) != "1":
        pytest.skip(f"real Codex invocation requires {CONSENT_ENV_VAR}=1 (not set) — skipping, not failing")

    pre_tickets = capture_snapshot(_REPO_ROOT)
    pre_config = snapshot_config_bytes(_REPO_ROOT)
    outcome = run_codex_replay(_REAL_FIXTURE_PATH, repo_root=_REPO_ROOT)
    post_tickets = capture_snapshot(_REPO_ROOT)
    post_config = snapshot_config_bytes(_REPO_ROOT)

    return {
        "outcome": outcome,
        "pre_tickets": pre_tickets,
        "post_tickets": post_tickets,
        "pre_config": pre_config,
        "post_config": post_config,
    }
