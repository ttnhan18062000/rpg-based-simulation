"""Validates the real, direct-experiment-grade Codex PostToolUse hook payload fixture.

Captured via TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE Step 11: an isolated scratch directory
outside this repo, a throwaway .codex/config.toml registering one PostToolUse hook that dumped its
real stdin verbatim, and one codex exec invocation that triggered a Bash tool call. This is
"direct_experiment" grade evidence, distinct from docs/ai/codex_capability_matrix.md's
documentation-citation-grade evidence (see that doc's §6).
"""
from __future__ import annotations

import json
from pathlib import Path

_FIXTURE_PATH = (
    Path(__file__).parent.parent
    / "fixtures"
    / "codex_hook_payloads"
    / "post_tool_use_stdin_capture.json"
)


def _load_fixture() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_file_exists_and_parses_as_json():
    assert _FIXTURE_PATH.is_file()
    data = _load_fixture()
    assert isinstance(data, dict)


def test_fixture_is_direct_experiment_grade():
    data = _load_fixture()
    assert data["capture_grade"] == "direct_experiment"


def test_fixture_hook_event_name_is_post_tool_use():
    data = _load_fixture()
    assert data["hook_event_name"] == "PostToolUse"
    assert data["raw_stdin_payload"]["hook_event_name"] == "PostToolUse"


def test_fixture_raw_payload_contains_documented_common_fields():
    """All 7 fields documented in codex_capability_matrix.md §1's common-field table for
    PostToolUse were confirmed present in the real capture, with zero discrepancy (Step 11's own
    recorded finding) — assert all 7, not a subset, since none were found missing."""
    data = _load_fixture()
    payload = data["raw_stdin_payload"]
    documented_common_fields = {
        "session_id",
        "transcript_path",
        "cwd",
        "hook_event_name",
        "model",
        "turn_id",
        "permission_mode",
    }
    assert documented_common_fields.issubset(payload.keys())


def test_fixture_raw_payload_contains_post_tool_use_specific_fields():
    """PostToolUse-specific fields beyond the common-field table, confirmed present in the real
    capture: tool_name, tool_input, tool_response, tool_use_id."""
    data = _load_fixture()
    payload = data["raw_stdin_payload"]
    post_tool_use_specific_fields = {"tool_name", "tool_input", "tool_response", "tool_use_id"}
    assert post_tool_use_specific_fields.issubset(payload.keys())


def test_fixture_schema_version_and_metadata_present():
    data = _load_fixture()
    assert data["fixture_schema_version"] == 1
    assert data["codex_cli_version"]
    assert data["captured_at_utc"]
    assert data["capture_method"]
