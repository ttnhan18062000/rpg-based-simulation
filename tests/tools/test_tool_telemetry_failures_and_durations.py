"""TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS: failed tool calls leave a row, and a duration comes from
this call's own stamp or is null, never from another call's.

The hooks are top-level scripts, driven the way Claude Code drives them: a subprocess fed a JSON payload on stdin,
`cwd` pointed at a temp git repo."""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tools.agent_working_paths import AGENT_MONITORING

_TOOLS = Path(__file__).resolve().parents[2] / "tools" / "agent-monitoring"
_PRE, _POST = _TOOLS / "pre_tool_hook.py", _TOOLS / "post_tool_hook.py"
_BRANCH = "test-branch"


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@e.x"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "T"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "-b", _BRANCH], check=True)
    (tmp_path / ".claude").mkdir()
    return tmp_path


def _run(script, cwd, payload):
    return subprocess.run([sys.executable, str(script)], input=json.dumps(payload), cwd=str(cwd),
                          capture_output=True, text=True, timeout=15)


def _rows(cwd):
    week = datetime.now(timezone.utc).strftime("%G-W%V")
    path = cwd / AGENT_MONITORING / "data" / week / f"{_BRANCH}.tools.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


def _post(session="s1", tool_use_id="t1", **extra):
    return {"session_id": session, "tool_use_id": tool_use_id, "tool_name": "Bash",
            "tool_input": {"command": "gh pr view 1"}, "tool_response": {}, **extra}


# --- failure rows ----------------------------------------------------------------------------------------------

def test_a_posttoolusefailure_payload_writes_one_failed_row_with_a_short_class(repo):
    _run(_POST, repo, _post(hook_event_name="PostToolUseFailure", error="Exit code 1\nError: Cannot find module 'x'",
                            is_interrupt=False, duration_ms=4187, tool_response=None))
    (row,) = _rows(repo)
    assert row["status"] == "failed" and row["error_class"] == "exit_1" and row["duration_ms"] == 4187
    assert "Cannot find module" not in json.dumps(row)  # the class, never the raw error text


@pytest.mark.parametrize("error, expected", [
    ("Exit code 128\nfatal: x", "exit_128"),
    ("Post https://api.github.com: net/http: TLS handshake timeout", "timeout"),
    ("x509: certificate signed by unknown authority", "tls"),
    ("HTTP 502 Bad Gateway", "http_5xx"),
    ("Permission denied (publickey)", "permission"),
    ("No such file or directory", "not_found"),
    ("something odd", "error"),
])
def test_error_classes_are_a_closed_set(repo, error, expected):
    _run(_POST, repo, _post(hook_event_name="PostToolUseFailure", error=error))
    assert _rows(repo)[-1]["error_class"] == expected


def test_an_interrupt_is_its_own_class(repo):
    _run(_POST, repo, _post(hook_event_name="PostToolUseFailure", error="aborted", is_interrupt=True))
    assert _rows(repo)[-1]["error_class"] == "interrupt"


def test_an_ok_row_has_no_error_class_and_the_old_is_error_path_still_fails(repo):
    _run(_POST, repo, _post(tool_use_id="a"))
    _run(_POST, repo, _post(tool_use_id="b", tool_response={"is_error": True, "error": "Exit code 2"}))
    ok, failed = _rows(repo)
    assert ok["status"] == "ok" and "error_class" not in ok
    assert failed["status"] == "failed" and failed["error_class"] == "exit_2"


# --- durations -------------------------------------------------------------------------------------------------

def test_interleaved_calls_get_their_own_durations(repo):
    """Two sessions, three calls in flight at once: the shared `.tool_start` used to give each the last writer's start."""
    _run(_PRE, repo, {"session_id": "s1", "tool_use_id": "slow"})
    time.sleep(0.6)
    _run(_PRE, repo, {"session_id": "s2", "tool_use_id": "fast"})
    _run(_PRE, repo, {"session_id": "s1", "tool_use_id": "fast"})  # same tool_use_id, other session: its own stamp
    _run(_POST, repo, _post(session="s2", tool_use_id="fast"))
    _run(_POST, repo, _post(session="s1", tool_use_id="slow"))
    fast, slow = _rows(repo)
    assert fast["duration_ms"] is not None and fast["duration_ms"] < 500
    assert slow["duration_ms"] is not None and slow["duration_ms"] >= 600


def test_a_stamp_is_used_once_and_removed(repo):
    _run(_PRE, repo, {"session_id": "s1", "tool_use_id": "t1"})
    _run(_POST, repo, _post())
    assert list((repo / ".claude" / "tool_starts").glob("*")) == []
    _run(_POST, repo, _post())  # a second post for the same id has no stamp
    assert _rows(repo)[1]["duration_ms"] is None


def test_an_unpairable_call_gets_null_never_a_guess(repo):
    _run(_PRE, repo, {"session_id": "s1", "tool_use_id": "someone-else"})
    _run(_POST, repo, _post(tool_use_id="mine"))
    assert _rows(repo)[0]["duration_ms"] is None
    no_id = _post()
    no_id.pop("tool_use_id")
    _run(_POST, repo, no_id)
    assert _rows(repo)[1]["duration_ms"] is None


def test_the_shared_tool_start_file_is_gone(repo):
    _run(_PRE, repo, {"session_id": "s1", "tool_use_id": "t1"})
    assert not (repo / ".claude" / ".tool_start").exists()
    assert (repo / ".claude" / ".current_session_id").read_text() == "s1"


def test_a_stale_stamp_is_swept(repo):
    stale = repo / ".claude" / "tool_starts" / "old.id"
    stale.parent.mkdir()
    stale.write_text("{}")
    old = time.time() - 3 * 24 * 3600
    os.utime(stale, (old, old))
    _run(_POST, repo, _post())
    assert not stale.exists()


def test_hostile_ids_cannot_escape_the_stamp_directory(repo):
    _run(_PRE, repo, {"session_id": "../../x", "tool_use_id": "../y"})
    assert not (repo / "y").exists() and not (repo.parent / "x").exists()
    assert len(list((repo / ".claude" / "tool_starts").glob("*"))) == 1
