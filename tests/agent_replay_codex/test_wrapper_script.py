"""Tests for tools/agent_replay_codex/wrapper_script.py (TCK-20260721-CODEX-REPLAY-PARITY, Step 3)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.agent_replay.fixture_envelope import load_fixture
from tools.agent_replay.runner import replay_slice

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "fixtures" / "agent_replay" / "TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml"
)
_WRAPPER_SCRIPT_PATH = _REPO_ROOT / "tools" / "agent_replay_codex" / "wrapper_script.py"


def test_scope_boundary_only_scope_through_review_phases_supported():
    fixture = load_fixture(_REAL_FIXTURE_PATH)
    assert {p.phase for p in fixture.phases} == {"Scope", "Investigate", "Plan", "Review"}


def test_wrapper_script_runs_standalone_and_writes_result(tmp_path):
    out_path = tmp_path / "result.json"
    result = subprocess.run(
        [
            sys.executable,
            str(_WRAPPER_SCRIPT_PATH),
            "--fixture",
            str(_REAL_FIXTURE_PATH),
            "--out",
            str(out_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    expected = replay_slice(load_fixture(_REAL_FIXTURE_PATH))
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written == {
        "final_status": expected.final_status,
        "phases_completed": expected.phases_completed,
    }
