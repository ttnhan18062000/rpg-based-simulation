"""Direct proof (monkeypatched spy) that no malformed-payload case ever reaches write_line
(Step 6)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent_codex_posttool_adapter import adapter, writer_bridge

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "codex_hook_payloads"
    / "post_tool_use_stdin_capture.json"
)
_TICKET_ID = "TCK-20260730-CODEX-POSTTOOL-ADAPTER"
_EXECUTION_ID = f"codex-{_TICKET_ID}-1700000000000-deadbeef"
_LIVE_ENV = {"CODEX_POSTTOOL_ADAPTER_LIVE_APPEND": "1"}


def _real_raw_payload() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))["raw_stdin_payload"]


def _missing_tool_name(raw):
    raw.pop("tool_name")
    return raw


def _wrong_hook_event(raw):
    raw["hook_event_name"] = "PreToolUse"
    return raw


def _non_dict_tool_input(raw):
    raw["tool_input"] = "not-a-dict"
    return raw


@pytest.mark.parametrize(
    "mutate", [_missing_tool_name, _wrong_hook_event, _non_dict_tool_input]
)
def test_malformed_payload_never_invokes_write_line(tmp_path, monkeypatch, mutate):
    calls: list = []

    def _fake_write_line(target_path, line):
        calls.append((target_path, line))
        return True

    monkeypatch.setattr(writer_bridge, "write_line", _fake_write_line)

    raw = mutate(_real_raw_payload())

    ok = adapter.process_post_tool_use(
        raw,
        target_path=tmp_path / "tools.jsonl",
        execution_id=_EXECUTION_ID,
        ticket_id=_TICKET_ID,
        env=_LIVE_ENV,
    )

    assert ok is False
    assert calls == []
