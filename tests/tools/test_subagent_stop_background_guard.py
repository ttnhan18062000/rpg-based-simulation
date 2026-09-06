"""Tests for tools/agent-monitoring/subagent_stop_background_guard.py
(TCK-20260904-TEST-SCOPER-HANG-GUARD).

The hook reads `payload["background_tasks"]` directly -- a harness-populated array describing
in-flight background work registered in the session, not a transcript-JSONL heuristic (see the
hook's own module docstring and tests/fixtures/claude_hook_payloads/subagent_stop_schema_capture.
json for why: both live-capture avenues for this ticket's Step 1 spike were blocked by this
sandbox's own auto-mode classifier, so the real payload shape was extracted directly from the
installed Claude Code binary's own validation schema instead).

Like every other hook script in tools/agent-monitoring/, this is a top-level script (not an
importable module of functions -- reading `sys.stdin` executes unconditionally on import), so
every test here drives it as a subprocess the way Claude Code itself does, mirroring
tests/tools/test_post_tool_hook.py's `_run_hook(cwd, payload)` pattern exactly.
"""
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_HOOK_PATH = _REPO_ROOT / "tools" / "agent-monitoring" / "subagent_stop_background_guard.py"


def _run_hook(cwd, payload):
    return subprocess.run(
        [sys.executable, str(_HOOK_PATH)],
        input=json.dumps(payload),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
    )


def _base_payload(**overrides):
    payload = {
        "session_id": "sess-guard-test",
        "transcript_path": "/tmp/does-not-matter/session.jsonl",
        "cwd": "/tmp/does-not-matter",
        "hook_event_name": "SubagentStop",
        "stop_hook_active": False,
        "agent_id": "agent-guard-test",
        "agent_transcript_path": "/tmp/does-not-matter/subagents/agent-guard-test.jsonl",
        "agent_type": "test-scoper",
    }
    payload.update(overrides)
    return payload


def test_hook_fires_for_still_running_background_task(tmp_path):
    payload = _base_payload(background_tasks=[
        {
            "id": "bc8huor3n",
            "type": "shell",
            "status": "running",
            "description": "Run scoped pytest sweep",
            "command": "pytest tests/tools/ -q",
        }
    ])

    result = _run_hook(tmp_path, payload)

    assert result.returncode == 2
    assert "Run scoped pytest sweep" in result.stdout
    output = json.loads(result.stdout)
    assert output["decision"] == "block"


def test_hook_allows_stop_when_background_task_already_polled_complete(tmp_path):
    payload = _base_payload(background_tasks=[])

    result = _run_hook(tmp_path, payload)

    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_hook_allows_stop_when_no_background_task_was_ever_started(tmp_path):
    payload = _base_payload()
    payload.pop("background_tasks", None)  # field absent entirely -- the common case

    result = _run_hook(tmp_path, payload)

    assert result.returncode == 0
    assert result.stdout.strip() == ""
    # No side-effect files: the hook needs no sidecar/state file at all (plan.md Step 2.7).
    assert list(tmp_path.iterdir()) == []


def test_hook_fails_open_on_malformed_or_missing_transcript(tmp_path):
    # Malformed stdin entirely (not valid JSON) -- the hook never reads a transcript file itself
    # (see module docstring: it reads payload["background_tasks"] directly, no file I/O), so the
    # only "malformed input" surface left is the stdin payload itself.
    result_malformed = subprocess.run(
        [sys.executable, str(_HOOK_PATH)],
        input="not valid json{{{",
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result_malformed.returncode == 0
    assert "Traceback" not in result_malformed.stderr

    # Completely empty stdin.
    result_empty = subprocess.run(
        [sys.executable, str(_HOOK_PATH)],
        input="",
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result_empty.returncode == 0
    assert "Traceback" not in result_empty.stderr

    # background_tasks present but malformed (not a list at all).
    payload_bad_shape = _base_payload(background_tasks="not-a-list")
    result_bad_shape = _run_hook(tmp_path, payload_bad_shape)
    assert result_bad_shape.returncode == 0
    assert "Traceback" not in result_bad_shape.stderr

    # background_tasks is a list but contains a non-dict entry.
    payload_bad_entry = _base_payload(background_tasks=["not-a-dict"])
    result_bad_entry = _run_hook(tmp_path, payload_bad_entry)
    assert result_bad_entry.returncode in (0, 2)  # must not raise either way
    assert "Traceback" not in result_bad_entry.stderr


def test_hook_respects_stop_hook_active_loop_prevention(tmp_path):
    # Per the harness's own documented intent (module docstring): a Stop/SubagentStop hook must
    # return success (allow) while stop_hook_active is true, even if background work the hook
    # would otherwise block on is still genuinely in flight -- otherwise it risks the harness's
    # own consecutive-block cap kicking in instead of a clean allow.
    payload = _base_payload(
        stop_hook_active=True,
        background_tasks=[
            {
                "id": "still-going",
                "type": "shell",
                "status": "running",
                "description": "A genuinely never-finishing background command",
                "command": "sleep 99999",
            }
        ],
    )

    result = _run_hook(tmp_path, payload)

    assert result.returncode == 0
    assert result.stdout.strip() == ""
