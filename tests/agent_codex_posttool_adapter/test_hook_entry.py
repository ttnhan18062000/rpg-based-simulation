from __future__ import annotations

import json
import os
from io import StringIO
from pathlib import Path
import subprocess
import sys

from tools.agent_codex_posttool_adapter.hook_entry import main

_ROOT = Path(__file__).parents[2]
_FIXTURE = _ROOT / "tests" / "fixtures" / "codex_hook_payloads" / "post_tool_use_stdin_capture.json"
_TICKET = "TCK-20260801-MONITORING-WRITER-STATUS-STALE"
_EXECUTION = f"codex-{_TICKET}-1-deadbeef"


def _env() -> dict[str, str]:
    return {
        **os.environ,
        "CODEX_POSTTOOL_ADAPTER_LIVE_APPEND": "1",
        "CODEX_HOOK_EXECUTION_ID": _EXECUTION,
        "CODEX_HOOK_TICKET_ID": _TICKET,
        "CODEX_HOOK_RUN_ID": _TICKET,
        "CODEX_HOOK_PHASE": "PostToolUse",
        "CODEX_HOOK_AGENT": "codex-posttool-hook",
        "CODEX_HOOK_SEQ_START": "1",
    }


def test_hook_entry_appends_a_redacted_identity_bound_scratch_record(tmp_path):
    payload = json.loads(_FIXTURE.read_text())["raw_stdin_payload"]
    (tmp_path / "agent-monitoring").mkdir()
    assert main(StringIO(json.dumps(payload)), _env(), tmp_path) == 0
    target = tmp_path / "agent-monitoring" / "tools.jsonl"
    [record] = [json.loads(line) for line in target.read_text().splitlines()]
    assert {key: record[key] for key in ("execution_id", "ticket_id", "run_id", "provider")} == {
        **{"execution_id": _EXECUTION, "ticket_id": _TICKET, "run_id": _TICKET}, "provider": "codex"
    }
    assert "tool_response" not in record


def test_hook_entry_fails_open_for_invalid_json_and_does_not_write(tmp_path):
    assert main(StringIO("not-json"), _env(), tmp_path) == 0
    target = tmp_path / "agent-monitoring" / "tools.jsonl"
    assert not target.exists()


def test_absolute_script_entrypoint_is_runnable_and_fail_open_for_invalid_input():
    entrypoint = _ROOT / "tools" / "agent_codex_posttool_adapter" / "hook_entry.py"
    result = subprocess.run(
        [sys.executable, str(entrypoint)], input="not-json", text=True, cwd=_ROOT, capture_output=True,
    )
    assert result.returncode == 0
