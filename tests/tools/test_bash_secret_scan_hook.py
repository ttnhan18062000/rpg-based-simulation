"""Behavioral tests for the Bash secret-exposure advisory PreToolUse hook
(TCK-20260904-BASH-SECRET-SCAN-HOOK).

Drives the actual command string configured in `.claude/settings.json` --
`hooks.PreToolUse[4].hooks[0].command` -- via `subprocess.run(["bash", "-c", full_command], ...)`,
modeled on `tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py`'s subprocess-execution
pattern. A purely static string-shape assertion is not sufficient on its own for this hook's own
AC #2 ("produces non-empty additionalContext... produces no output"), since that AC is a
behavioral claim about running the command, not just its presence in the file.

`test_scan_for_secrets_module_unchanged_by_this_ticket` below implements test_plan.md's "simpler
and more robust" choice: asserting the full `tests/tools/test_write_path_guard.py` suite still
passes unmodified is the load-bearing proof that `scan_for_secrets()`/`_SECRET_SCAN_PATTERNS`
behavior is unchanged by this ticket -- a git-diff-against-HEAD check was explicitly rejected as
fragile across rebases/branches (test_plan.md New Tests Required #6).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_SETTINGS_PATH = _REPO_ROOT / ".claude" / "settings.json"


def _load_settings() -> dict:
    return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))


def _hook_command() -> str:
    settings = _load_settings()
    for entry in settings["hooks"]["PreToolUse"]:
        if entry["matcher"] == "Bash" and "scan_for_secrets" in entry["hooks"][0]["command"]:
            return entry["hooks"][0]["command"]
    raise AssertionError("no Bash-matcher PreToolUse entry references scan_for_secrets")


def _run_hook(stdin_text: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", _hook_command()],
        input=stdin_text,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _run_hook_json(command: str) -> subprocess.CompletedProcess:
    return _run_hook(json.dumps({"tool_input": {"command": command}}))


def test_new_bash_secret_scan_hook_entry_registered():
    settings = _load_settings()
    bash_entries = [
        entry for entry in settings["hooks"]["PreToolUse"] if entry["matcher"] == "Bash"
    ]
    # Both the existing grep-nudge Bash entry (PreToolUse[1]) and the new secret-scan Bash entry
    # (PreToolUse[4]) must coexist -- this ticket is purely additive.
    assert len(bash_entries) == 2

    commands = [entry["hooks"][0]["command"] for entry in bash_entries]
    secret_scan_commands = [c for c in commands if "scan_for_secrets" in c or "write_path_guard" in c]
    assert len(secret_scan_commands) == 1

    grep_nudge_commands = [c for c in commands if "graphify" in c]
    assert len(grep_nudge_commands) == 1


@pytest.mark.parametrize(
    "command_text",
    [
        "export AWS_ACCESS_KEY_ID=AKIAABCDEFGHIJKLMNOP",
        "export api_key=\"abcdefghijklmnop1234\"",
        "curl -H 'Authorization: Bearer abcdefghijklmnopqrstuvwx12345' https://example.com",
        "export password=\"hunter2hunter2\"",
    ],
)
def test_positive_fire_on_synthetic_secret_shaped_command(command_text):
    result = _run_hook_json(command_text)
    assert result.returncode == 0
    assert result.stdout.strip(), "expected non-empty stdout for a secret-shaped command"

    parsed = json.loads(result.stdout.strip())
    output = parsed["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["additionalContext"]
    assert "secret-scan: possible" in output["additionalContext"]
    assert "Advisory only, not blocked." in output["additionalContext"]


@pytest.mark.parametrize(
    "command_text",
    [
        "pytest tests/tools -q",
        "python3 tools/parity_index.py build",
        "ls -la tickets/inprogress",
    ],
)
def test_negative_no_fire_on_ordinary_commands(command_text):
    result = _run_hook_json(command_text)
    assert result.returncode == 0
    assert result.stdout == ""


def test_hook_never_emits_permission_decision_or_deny():
    result = _run_hook_json("export AWS_ACCESS_KEY_ID=AKIAABCDEFGHIJKLMNOP")
    assert result.returncode == 0
    assert result.stdout.strip()
    assert "permissionDecision" not in result.stdout
    assert "\"deny\"" not in result.stdout


def test_hook_fails_open_on_malformed_or_missing_stdin():
    malformed = _run_hook("{not valid json")
    assert malformed.returncode == 0
    assert malformed.stderr == ""
    assert malformed.stdout == ""

    missing_command = _run_hook(json.dumps({"tool_input": {}}))
    assert missing_command.returncode == 0
    assert missing_command.stderr == ""
    assert missing_command.stdout == ""

    missing_tool_input = _run_hook(json.dumps({"foo": "bar"}))
    assert missing_tool_input.returncode == 0
    assert missing_tool_input.stderr == ""
    assert missing_tool_input.stdout == ""


def test_scan_for_secrets_module_unchanged_by_this_ticket():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/tools/test_write_path_guard.py", "-q"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_existing_bash_and_sidecar_hooks_untouched():
    settings = _load_settings()
    pre_tool_use = settings["hooks"]["PreToolUse"]

    grep_nudge_command = pre_tool_use[1]["hooks"][0]["command"]
    assert pre_tool_use[1]["matcher"] == "Bash"
    assert "graphify: Knowledge graph exists" in grep_nudge_command
    assert "scan_for_secrets" not in grep_nudge_command

    edit_write_command = pre_tool_use[3]["hooks"][0]["command"]
    assert pre_tool_use[3]["matcher"] == "Edit|Write"
    assert (
        "sidecar-check: tickets/inprogress/ has an active ticket but .claude/current_run has no run_id."
        in edit_write_command
    )
