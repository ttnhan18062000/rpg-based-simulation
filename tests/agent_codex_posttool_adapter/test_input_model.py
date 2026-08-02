"""Tests for tools/agent_codex_posttool_adapter/input_model.py (Step 1)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.agent_codex_posttool_adapter.errors import (
    HookEventNotEvidencedError,
    PayloadValidationError,
)
from tools.agent_codex_posttool_adapter.input_model import (
    CodexPostToolUsePayload,
    parse_payload,
)

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "codex_hook_payloads"
    / "post_tool_use_stdin_capture.json"
)


def _real_raw_payload() -> dict:
    data = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return data["raw_stdin_payload"]


def test_real_fixture_parses_into_adapter_input_model():
    payload = parse_payload(_real_raw_payload())
    assert isinstance(payload, CodexPostToolUsePayload)
    assert payload.session_id == "019f894e-cded-7242-bfda-05d6f7b8fa58"
    assert payload.tool_name == "Bash"
    assert payload.hook_event_name == "PostToolUse"
    assert payload.tool_input == {"command": "ls -la ."}
    assert isinstance(payload.tool_response, str)


@pytest.mark.parametrize(
    "missing_field",
    ["session_id", "tool_name", "hook_event_name", "tool_input", "tool_response"],
)
def test_missing_required_field_fails_safely_no_write(missing_field):
    raw = _real_raw_payload()
    del raw[missing_field]
    with pytest.raises(PayloadValidationError):
        parse_payload(raw)


def test_non_post_tool_use_hook_event_name_rejected():
    raw = _real_raw_payload()
    raw["hook_event_name"] = "PreToolUse"
    with pytest.raises(HookEventNotEvidencedError):
        parse_payload(raw)


def test_malformed_json_or_wrong_shape_fails_safely():
    with pytest.raises(PayloadValidationError):
        parse_payload("not-a-dict")

    with pytest.raises(PayloadValidationError):
        parse_payload(["also", "not", "a", "dict"])

    raw = _real_raw_payload()
    raw["tool_input"] = "not-a-dict"
    with pytest.raises(PayloadValidationError):
        parse_payload(raw)
