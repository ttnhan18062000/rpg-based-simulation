"""Tests for tools/agent_codex_posttool_adapter/live_gate.py (Step 4), plus the adapter's
end-to-end live-gate enforcement (Step 6)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent_codex_posttool_adapter.adapter import process_post_tool_use
from tools.agent_codex_posttool_adapter.errors import LiveAppendNotGrantedError
from tools.agent_codex_posttool_adapter.live_gate import LIVE_APPEND_ENV_VAR, require_live_append

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "codex_hook_payloads"
    / "post_tool_use_stdin_capture.json"
)
_TICKET_ID = "TCK-20260730-CODEX-POSTTOOL-ADAPTER"
_EXECUTION_ID = f"codex-{_TICKET_ID}-1700000000000-deadbeef"


def _real_raw_payload() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))["raw_stdin_payload"]


@pytest.mark.parametrize(
    "env", [{}, {LIVE_APPEND_ENV_VAR: "true"}, {LIVE_APPEND_ENV_VAR: "yes"}, {LIVE_APPEND_ENV_VAR: "0"}]
)
def test_require_live_append_refuses_without_exact_value(env):
    with pytest.raises(LiveAppendNotGrantedError):
        require_live_append(env)


def test_require_live_append_grants_on_exact_value():
    require_live_append({LIVE_APPEND_ENV_VAR: "1"})


def test_append_refused_without_explicit_live_gate(tmp_path):
    target_path = tmp_path / "tools.jsonl"

    ok = process_post_tool_use(
        _real_raw_payload(),
        target_path=target_path,
        execution_id=_EXECUTION_ID,
        ticket_id=_TICKET_ID,
        env={},
    )

    assert ok is False
    assert not target_path.exists()


def test_append_succeeds_against_a_tmp_path_target_when_live_gate_is_set(tmp_path):
    target_path = tmp_path / "tools.jsonl"

    ok = process_post_tool_use(
        _real_raw_payload(),
        target_path=target_path,
        execution_id=_EXECUTION_ID,
        ticket_id=_TICKET_ID,
        env={LIVE_APPEND_ENV_VAR: "1"},
    )

    assert ok is True
    lines = target_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["provider"] == "codex"
    assert record["ticket_id"] == _TICKET_ID
