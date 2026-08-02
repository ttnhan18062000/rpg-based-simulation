"""Typed input model for a captured Codex `PostToolUse` hook stdin payload (Step 1).

`parse_payload` reads only `raw_stdin_payload`'s own fields — it never reads the fixture's outer
envelope (`fixture_schema_version`, `capture_grade`, `codex_cli_version`, `captured_at_utc`,
`capture_method`). Callers unwrap the envelope before calling this function.
"""
from __future__ import annotations

from dataclasses import dataclass

from tools.agent_codex_pilot_guardrails.enabled_surface import EVIDENCED_HOOK_EVENTS

from .errors import HookEventNotEvidencedError, PayloadValidationError

_REQUIRED_FIELDS = ("session_id", "tool_name", "hook_event_name", "tool_input", "tool_response")


@dataclass(frozen=True)
class CodexPostToolUsePayload:
    session_id: str
    tool_name: str
    tool_input: dict
    tool_response: object
    hook_event_name: str


def parse_payload(raw: dict) -> CodexPostToolUsePayload:
    if not isinstance(raw, dict):
        raise PayloadValidationError(f"raw_stdin_payload must be a dict, got {type(raw).__name__}")

    for field in _REQUIRED_FIELDS:
        if field not in raw:
            raise PayloadValidationError(f"raw_stdin_payload missing required field: {field!r}")

    tool_input = raw["tool_input"]
    if not isinstance(tool_input, dict):
        raise PayloadValidationError(
            f"raw_stdin_payload['tool_input'] must be a dict, got {type(tool_input).__name__}"
        )

    hook_event_name = raw["hook_event_name"]
    if hook_event_name not in EVIDENCED_HOOK_EVENTS:
        raise HookEventNotEvidencedError(
            f"hook_event_name {hook_event_name!r} is not in the evidenced hook-event set "
            f"{sorted(EVIDENCED_HOOK_EVENTS)}"
        )

    return CodexPostToolUsePayload(
        session_id=raw["session_id"],
        tool_name=raw["tool_name"],
        tool_input=tool_input,
        tool_response=raw["tool_response"],
        hook_event_name=hook_event_name,
    )
