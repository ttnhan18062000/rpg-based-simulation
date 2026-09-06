"""Structural test for .claude/settings.json's `hooks` block (TCK-20260904-TEST-SCOPER-HANG-GUARD).

Placement note: this is a new file rather than an addition to
tests/agent_orchestration/test_contract_structure.py, deliberately. That file's own tests assert
content governed by the agent-orchestration/ contract bundle (contract.yaml, hook-events.yaml,
hook-surface-policy.yaml, roles/, etc. -- everything `agent_orchestration.loader.load_contract`
parses). `.claude/settings.json` is a real, separate, Claude-Code-native config file that the
contract bundle does not govern or load at all -- it is read directly here, by plain `json.load`,
with no dependency on `agent_orchestration.loader` or its PYTHONPATH requirements. Folding this
into test_contract_structure.py would misrepresent `.claude/settings.json` as contract-governed
content when it structurally is not.
"""
import json
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_SETTINGS_PATH = _REPO_ROOT / ".claude" / "settings.json"


def _load_settings() -> dict:
    return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))


def test_new_hook_event_key_not_previously_wired():
    settings = _load_settings()
    hooks = settings["hooks"]

    # Proves this is a genuinely new deterministic surface, not a restatement of the existing
    # PreToolUse/PostToolUse writers (AC #2).
    assert "SubagentStop" in hooks
    assert {"PreToolUse", "PostToolUse"} <= set(hooks)

    matcher_groups = hooks["SubagentStop"]
    assert isinstance(matcher_groups, list) and len(matcher_groups) == 1
    assert matcher_groups[0]["matcher"] == "*"

    commands = [entry["command"] for entry in matcher_groups[0]["hooks"]]
    assert any("subagent_stop_background_guard.py" in command for command in commands)


def test_subagent_stop_command_not_suffixed_with_swallowing_fallback():
    # Critical deviation from every existing hook command in this file (plan.md Step 3): a
    # trailing `|| true` would unconditionally yield exit status 0 regardless of the script's own
    # exit code, silently swallowing the deliberate exit-2 block signal this ticket exists to
    # produce. Every existing PreToolUse/PostToolUse command DOES end in `|| true` (advisory-only,
    # by design) -- this new command must not, or the guard would parse correctly but never
    # actually block anything.
    settings = _load_settings()
    matcher_groups = settings["hooks"]["SubagentStop"]
    for group in matcher_groups:
        for entry in group["hooks"]:
            assert "|| true" not in entry["command"], (
                f"SubagentStop hook command must not swallow its own exit code: {entry['command']!r}"
            )


def test_subagent_stop_hook_references_script_that_exists():
    settings = _load_settings()
    matcher_groups = settings["hooks"]["SubagentStop"]
    script_path = _REPO_ROOT / "tools" / "agent-monitoring" / "subagent_stop_background_guard.py"
    assert script_path.exists()

    commands = [
        entry["command"]
        for group in matcher_groups
        for entry in group["hooks"]
    ]
    assert any("tools/agent-monitoring/subagent_stop_background_guard.py" in c for c in commands)


def test_existing_hook_writers_untouched():
    # Do NOT touch: the permissions.allow block or the existing PreToolUse/PostToolUse array
    # contents (plan.md Step 3's explicit constraint).
    settings = _load_settings()
    assert len(settings["hooks"]["PreToolUse"]) == 4
    assert len(settings["hooks"]["PostToolUse"]) == 4
    assert "permissions" in settings
    assert "allow" in settings["permissions"]


def test_edit_write_hook_reads_scoped_sidecar_via_env_var():
    # TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE, AC #1 / AC #4: the Edit|Write PreToolUse hook's
    # RUN_ID=$(...) subshell must read the session-scoped sidecar file first (falling back to the
    # unscoped file), mirroring tools/retrieval_cache.py::read_current_run_sidecar()'s preference
    # order rather than the old unscoped-only read.
    settings = _load_settings()
    command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]

    assert "os.environ.get('CLAUDE_CODE_SESSION_ID','')" in command
    assert ".claude/current_run.'+sid" in command
    assert "os.path.exists(" in command
    assert "else '.claude/current_run'" in command

    # The old single-branch (unscoped-only) form must be fully replaced, not merely appended
    # alongside the new one.
    old_form = (
        "RUN_ID=$(python3 -c \\\"import json; "
        "print(json.load(open('.claude/current_run')).get('run_id') or '')\\\""
    )
    assert old_form not in command


def test_edit_write_hook_still_fail_open_and_advisory():
    # Regression guard (test_plan.md #2): the edit must not drop or relocate the fail-open
    # wrapper on either subshell, nor reword the advisory reminder text.
    settings = _load_settings()
    command = settings["hooks"]["PreToolUse"][3]["hooks"][0]["command"]

    file_subshell = command.split("RUN_ID=$(", 1)[0]
    assert "FILE=$(python3 -c" in file_subshell
    assert "2>/dev/null || true" in file_subshell

    run_id_subshell = command.split("RUN_ID=$(", 1)[1]
    assert "2>/dev/null || true" in run_id_subshell

    assert (
        "sidecar-check: tickets/inprogress/ has an active ticket but .claude/current_run has no run_id."
        in command
    )


def test_edit_write_hook_json_still_valid_after_edit():
    # Regression guard (test_plan.md #3): the file must still parse as valid JSON with its
    # top-level shape intact after the RUN_ID segment edit.
    settings = _load_settings()
    assert "permissions" in settings
    assert "allow" in settings["permissions"]
    assert {"PreToolUse", "PostToolUse", "SubagentStop"} <= set(settings["hooks"])
