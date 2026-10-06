"""TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES: the settings.json hook commands under tools/agent-monitoring/ resolve the
repo top level, so a session whose cwd is a subdirectory still writes its tools.jsonl row (before, `python3 tools/...` from a
subdirectory found no script and `|| true` hid it).

Runs the real settings.json command in a throwaway detached worktree of this repo; nothing is written to the real data tree."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.agent_working_paths import AGENT_MONITORING

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())["hooks"]
PAYLOAD = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}, "tool_response": {}, "session_id": "subdir-probe"})


def _command(event: str, script: str) -> str:
    found = [h["command"] for g in SETTINGS[event] for h in g["hooks"] if script in h["command"]]
    assert len(found) == 1, (event, script, found)
    return found[0]


@pytest.mark.parametrize("event,script", [
    ("PreToolUse", "pre_tool_hook.py"), ("PreToolUse", "cd_prefix_advisory_hook.py"), ("PostToolUse", "post_tool_hook.py"),
    ("PostToolUse", "retro_nudge_hook.py"), ("PostToolUse", "epic_staleness_check.py"),
])
def test_agent_monitoring_hook_commands_resolve_the_repo_top_level(event, script):
    command = _command(event, script)
    assert command.startswith("R=$(git rev-parse --show-toplevel") and f'test -f "$R/tools/agent-monitoring/{script}"' in command
    assert f'cd "$R" && python3 tools/agent-monitoring/{script}' in command
    assert command.endswith("|| true")


@pytest.fixture
def worktree(tmp_path):
    wt = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), "HEAD"], cwd=REPO_ROOT, check=True)
    yield wt
    subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=REPO_ROOT, check=False)


def _tools_shards(wt: Path) -> set[Path]:
    return set((wt / AGENT_MONITORING / "data").glob("*/*tools.jsonl"))


@pytest.mark.parametrize("subdir", ["", "docs", "tools/agent-monitoring"])
def test_post_tool_hook_command_writes_a_row_from_a_subdirectory(worktree, subdir):
    before = _tools_shards(worktree)
    result = subprocess.run(["bash", "-c", _command("PostToolUse", "post_tool_hook.py")], cwd=worktree / subdir,
                            input=PAYLOAD, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0
    new = _tools_shards(worktree) - before
    assert len(new) == 1 and "subdir-probe" in next(iter(new)).read_text()
    assert not (worktree / subdir / "agent-working").exists() or subdir == ""  # nothing stray under the subdirectory
    assert not (worktree / subdir / ".claude").exists() or subdir == ""
