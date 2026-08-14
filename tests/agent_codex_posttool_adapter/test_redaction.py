"""Tests for redaction.py and record_builder.py (Step 2), plus AC #2's provider-literal check
(Step 6's verify list)."""
from __future__ import annotations

import json
from pathlib import Path

from tools.agent_codex_posttool_adapter.input_model import parse_payload
from tools.agent_codex_posttool_adapter.record_builder import build_record
from tools.agent_codex_posttool_adapter.redaction import summarize_tool_input

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "codex_hook_payloads"
    / "post_tool_use_stdin_capture.json"
)
_TICKET_ID = "TCK-20260730-CODEX-POSTTOOL-ADAPTER"
_EXECUTION_ID = f"codex-{_TICKET_ID}-1700000000000-deadbeef"


def _real_raw_payload() -> dict:
    data = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return data["raw_stdin_payload"]


def _build_real_record(**overrides) -> dict:
    payload = parse_payload(_real_raw_payload())
    kwargs = {
        "execution_id": _EXECUTION_ID,
        "provider": "codex",
        "ticket_id": _TICKET_ID,
        "now": "2026-07-30T00:00:00Z",
    }
    kwargs.update(overrides)
    return build_record(payload, **kwargs)


def test_output_record_omits_transcript_path_cwd_model_permission_mode_turn_id_tool_use_id():
    record = _build_real_record()
    for field in ("transcript_path", "cwd", "model", "permission_mode", "turn_id", "tool_use_id"):
        assert field not in record


def test_tool_response_content_never_appears_in_output_record():
    raw = _real_raw_payload()
    record = _build_real_record()
    serialized = json.dumps(record)
    assert raw["tool_response"] not in serialized
    assert set(record.keys()) == {
        "session_id",
        "run_id",
        "seq",
        "phase",
        "agent",
        "ts",
        "tool",
        "input_summary",
        "status",
        "duration_ms",
        "execution_id",
        "provider",
        "ticket_id",
    }
    assert record["status"] == "ok"


def test_tool_input_summary_is_truncated_and_field_allowlisted():
    assert summarize_tool_input("Bash", {"command": "x" * 200}) == ("x" * 200)[:80]
    assert summarize_tool_input("Read", {"file_path": "y" * 200}) == ("y" * 200)[:120]
    assert summarize_tool_input("Agent", {"description": "z" * 200}) == ("z" * 200)[:80]
    assert summarize_tool_input("mcp__knowledge-search__search_docs", {"query": "q"}) == "query='q'"

    record = _build_real_record()
    assert record["input_summary"] == "ls -la ."


def test_output_record_carries_provider_codex_literal():
    record = _build_real_record()
    assert record["provider"] == "codex"
