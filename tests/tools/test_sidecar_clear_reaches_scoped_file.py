"""Behavioural tests for TCK-20260928-SIDECAR-CLEAR-MISSES-SESSION-SCOPED-FILE.

`.claude/workflows/{create-tickets,implement-ticket,implement-epic}.js` each end their own run by
clearing `.claude/current_run` to `{}` -- but `tools/agent-monitoring/post_tool_hook.py` reads
ONLY the per-session-scoped `.claude/current_run.<session_id>` file whenever the hook payload
carries a `session_id` (always, for real hooks; `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s own
deliberate no-fallback rule). A clear that only empties the shared file is a silent no-op for real
attribution. The three workflows' own text-pin tests
(`test_current_run_sidecar_orchestrator.py`, `test_epic_create_tickets_sidecar_orchestrator.py`,
`test_create_tickets_sidecar_reset_and_failure_visibility.py`) only prove the shared `clearSidecar`
helper's SOURCE TEXT looks right -- this file proves the actual command it runs really does clear
what `post_tool_hook.py` reads, by running both the real command and the pre-fix command through
the real hook end to end, mirroring `test_post_tool_hook.py`'s own established subprocess-driven
pattern (the hook is a top-level script, not importable as functions).
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_HOOK_PATH = _MONITORING_TOOLS_DIR / "post_tool_hook.py"
_WORKFLOWS_DIR = _REPO_ROOT / ".claude" / "workflows"

_TEST_BRANCH = "test-branch"


def _ensure_git_repo_on_test_branch(cwd) -> None:
    if (cwd / ".git").exists():
        return
    subprocess.run(["git", "init", "-q", str(cwd)], check=True)
    subprocess.run(["git", "-C", str(cwd), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(cwd), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(cwd), "checkout", "-q", "-b", _TEST_BRANCH], check=True)


def _payload(session_id):
    return {
        "session_id": session_id,
        "tool_name": "Bash",
        "tool_input": {"command": "echo probe"},
        "tool_response": {},
    }


def _run_hook(cwd, payload):
    _ensure_git_repo_on_test_branch(cwd)
    return subprocess.run(
        [sys.executable, str(_HOOK_PATH)],
        input=json.dumps(payload),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
    )


def _last_tools_row(cwd):
    iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
    tools_file = cwd / "agent-monitoring" / "data" / iso_week / f"{_TEST_BRANCH}.tools.jsonl"
    lines = [l for l in tools_file.read_text().splitlines() if l.strip()]
    return json.loads(lines[-1])


def _write_stale_scoped_sidecar(cwd, session_id):
    scoped = cwd / ".claude" / f"current_run.{session_id}"
    scoped.parent.mkdir(parents=True, exist_ok=True)
    scoped.write_text(json.dumps({
        "run_id": "TCK-STALE-FINISHED-RUN", "seq": 7, "phase": "Implement", "agent": "claude",
    }))
    return scoped


def _clear_sidecar_command_from(workflow_filename: str) -> str:
    """Extract the exact shell command inside `clearSidecar()`'s `bash()` call from a real
    workflow `.js` file, so this test runs the REAL command rather than a re-implementation that
    could silently drift from it."""
    path = _WORKFLOWS_DIR / workflow_filename
    text = path.read_text(encoding="utf-8")
    start = text.index("const clearSidecar = async () => {")
    body_start = text.index("`", start) + 1
    body_end = text.index("`", body_start)
    return text[body_start:body_end]


_OLD_PRE_FIX_COMMAND = "printf '{}' > .claude/current_run"


def _run_clear_command(cwd, session_id, command):
    return subprocess.run(
        ["bash", "-c", command],
        cwd=str(cwd),
        env={**os.environ, "CLAUDE_CODE_SESSION_ID": session_id},
        capture_output=True,
        text=True,
        timeout=10,
    )


@pytest.mark.parametrize("workflow_filename", [
    "create-tickets.js", "implement-ticket.js", "implement-epic.js",
])
def test_real_clear_sidecar_command_makes_post_tool_hook_read_null(tmp_path, workflow_filename):
    session_id = f"sess-{workflow_filename}"
    _write_stale_scoped_sidecar(tmp_path, session_id)

    command = _clear_sidecar_command_from(workflow_filename)
    clear_result = _run_clear_command(tmp_path, session_id, command)
    assert clear_result.returncode == 0, clear_result.stderr

    hook_result = _run_hook(tmp_path, _payload(session_id))
    assert hook_result.returncode == 0, hook_result.stderr
    record = _last_tools_row(tmp_path)
    assert record["run_id"] is None, (
        f"{workflow_filename}'s real clearSidecar() command did not clear the file "
        f"post_tool_hook.py actually reads — attribution stayed stale: {record}"
    )


def test_old_shared_file_only_clear_command_is_a_no_op_for_attribution(tmp_path):
    # The exact pre-fix shape (implement-ticket.js's own two former clears, and create-tickets.js's
    # first-pass writeMonitoring Step 0): only ever emptied the SHARED file. Proves the real bug —
    # this command must NOT clear attribution, since post_tool_hook.py never reads the shared file
    # once a session_id is present.
    session_id = "sess-old-command"
    _write_stale_scoped_sidecar(tmp_path, session_id)

    clear_result = _run_clear_command(tmp_path, session_id, _OLD_PRE_FIX_COMMAND)
    assert clear_result.returncode == 0, clear_result.stderr

    hook_result = _run_hook(tmp_path, _payload(session_id))
    assert hook_result.returncode == 0, hook_result.stderr
    record = _last_tools_row(tmp_path)
    assert record["run_id"] == "TCK-STALE-FINISHED-RUN", (
        "the old shared-file-only clear command must NOT actually clear attribution — proving "
        "it was a silent no-op is the whole point of this ticket"
    )


def test_real_clear_command_also_still_empties_the_shared_file(tmp_path):
    # The shared file still matters for the one defensive fallback path (no session_id at all in
    # the hook payload) — the real fix must not regress that by dropping the shared-file write.
    session_id = "sess-shared-check"
    _write_stale_scoped_sidecar(tmp_path, session_id)
    shared_path = tmp_path / ".claude" / "current_run"
    shared_path.write_text(json.dumps({"run_id": "TCK-STALE-FINISHED-RUN", "seq": 7}))

    command = _clear_sidecar_command_from("create-tickets.js")
    clear_result = _run_clear_command(tmp_path, session_id, command)
    assert clear_result.returncode == 0, clear_result.stderr

    assert json.loads(shared_path.read_text()) == {}
