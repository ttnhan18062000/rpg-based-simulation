"""Integration tests for the Edit|Write PreToolUse hook's session-scoped sidecar read
(TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE).

These tests drive the actual command string configured in `.claude/settings.json` --
`hooks.PreToolUse[3].hooks[0].command` -- either by extracting and directly executing the inner
`python3 -c` RUN_ID snippet (tests #1/#2/#4/#5), or by running the full command through `bash -c`
(tests #3/#6, where the outer fail-open wrapper's behavior is itself under test). See plan.md Step
3 for why the two techniques are not interchangeable: the bare extracted snippet has no shell-level
`2>/dev/null || true` around it, so it raises an uncaught `FileNotFoundError`/traceback when the
sidecar file it tries to `open()` does not exist -- that wrapper only exists one layer up, around
the full `RUN_ID=$(...)` subshell inside the full command string.
"""
import json
import os
import re
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SETTINGS_PATH = _REPO_ROOT / ".claude" / "settings.json"


def _load_settings() -> dict:
    return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))


def _extract_run_id_snippet() -> str:
    settings = _load_settings()
    command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]
    match = re.search(
        r'RUN_ID=\$\(python3 -c "(.*?)" 2>/dev/null \|\| true\)', command
    )
    assert match is not None, "RUN_ID snippet not found in settings.json command string"
    return match.group(1)


def _write_sidecar(base: Path, name: str, run_id: str) -> None:
    claude_dir = base / ".claude"
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / name).write_text(json.dumps({"run_id": run_id}), encoding="utf-8")


def _run_snippet(cwd: Path, env: dict) -> str:
    result = subprocess.run(
        ["python3", "-c", _extract_run_id_snippet()],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_run_id_resolution_prefers_scoped_over_unscoped_when_scoped_exists(tmp_path):
    _write_sidecar(tmp_path, "current_run.sess-1", "TCK-REAL")
    _write_sidecar(tmp_path, "current_run", "TCK-STALE-FOREIGN")

    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": "sess-1"}
    assert _run_snippet(tmp_path, env) == "TCK-REAL"


def test_run_id_resolution_falls_back_to_unscoped_when_scoped_absent(tmp_path):
    _write_sidecar(tmp_path, "current_run", "TCK-UNSCOPED")

    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": "sess-nomatch"}
    assert _run_snippet(tmp_path, env) == "TCK-UNSCOPED"


def test_run_id_resolution_empty_when_both_absent(tmp_path):
    # Cannot use the bare-extracted-snippet technique here: with no sidecar files present at all,
    # the bare snippet's own open(path) call raises an uncaught FileNotFoundError -- there is no
    # shell-level `2>/dev/null || true` around a bare extracted snippet to catch it. Use the full
    # command via bash -c instead, which does have that wrapper.
    settings = _load_settings()
    full_command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]

    tickets_dir = tmp_path / "tickets" / "inprogress"
    tickets_dir.mkdir(parents=True)
    (tickets_dir / "fake.md").write_text("placeholder", encoding="utf-8")

    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": "sess-none"}
    result = subprocess.run(
        ["bash", "-c", full_command],
        input=json.dumps({"tool_input": {"file_path": "a/src/foo.py"}}),
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert (
        "sidecar-check: tickets/inprogress/ has an active ticket but .claude/current_run has no run_id."
        in result.stdout
    )


def test_run_id_resolution_empty_when_session_id_env_var_unset(tmp_path):
    _write_sidecar(tmp_path, "current_run", "TCK-UNSCOPED")

    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
    assert _run_snippet(tmp_path, env) == "TCK-UNSCOPED"


def test_two_concurrent_sessions_resolve_to_their_own_run_id(tmp_path):
    _write_sidecar(tmp_path, "current_run.sess-a", "TCK-A")
    _write_sidecar(tmp_path, "current_run.sess-b", "TCK-B")
    _write_sidecar(tmp_path, "current_run", "TCK-STALE-FOREIGN")

    env_a = {**os.environ, "CLAUDE_CODE_SESSION_ID": "sess-a"}
    env_b = {**os.environ, "CLAUDE_CODE_SESSION_ID": "sess-b"}

    result_a = _run_snippet(tmp_path, env_a)
    result_b = _run_snippet(tmp_path, env_b)

    assert result_a == "TCK-A"
    assert result_b == "TCK-B"
    assert result_a != "TCK-STALE-FOREIGN"
    assert result_b != "TCK-STALE-FOREIGN"


def test_malformed_or_missing_sidecar_json_degrades_to_empty_not_traceback(tmp_path):
    settings = _load_settings()
    full_command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]

    tickets_dir = tmp_path / "tickets" / "inprogress"
    tickets_dir.mkdir(parents=True)
    (tickets_dir / "fake.md").write_text("placeholder", encoding="utf-8")

    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "current_run.sess-bad").write_text("{not valid json", encoding="utf-8")

    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": "sess-bad"}
    result = subprocess.run(
        ["bash", "-c", full_command],
        input=json.dumps({"tool_input": {"file_path": "a/src/foo.py"}}),
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert result.stderr == ""
