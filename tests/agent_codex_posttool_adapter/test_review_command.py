from __future__ import annotations

from pathlib import Path

from tools.agent_codex_posttool_adapter.command import render_review_command


def test_review_command_uses_only_absolute_venv_and_entrypoint_paths(tmp_path):
    command = render_review_command(tmp_path)
    assert str((tmp_path / ".venv" / "bin" / "python3").resolve()) in command
    assert str((tmp_path / "tools" / "agent_codex_posttool_adapter" / "hook_entry.py").resolve()) in command
    assert " python3" not in command
    assert "${" not in command
    assert "$(" not in command
