"""Tests for tools/agent-monitoring/session_start_handover_hook.py.

TCK-20260921-SESSION-CONTEXT-RESET-TRIAL. The hook script's own `main()` reads stdin/prints JSON —
tested via real subprocess invocation (cheap, no filesystem-outside-tmp_path risk) for the I/O
contract, and via `build_additional_context()` directly for the listing logic itself.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_HOOK_SCRIPT = _REPO_ROOT / "tools" / "agent-monitoring" / "session_start_handover_hook.py"
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from session_start_handover_hook import build_additional_context  # noqa: E402


def _run_hook(payload: dict, cwd: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(_HOOK_SCRIPT)],
        input=json.dumps(payload), capture_output=True, text=True, cwd=str(cwd), timeout=10,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_build_additional_context_empty_when_dir_missing(tmp_path):
    assert build_additional_context(tmp_path / "does-not-exist") == ""


def test_build_additional_context_empty_when_dir_has_no_md_files(tmp_path):
    d = tmp_path / "handover"
    d.mkdir()
    (d / "readme.txt").write_text("not markdown")
    assert build_additional_context(d) == ""


def test_build_additional_context_lists_paths_and_first_line_titles(tmp_path):
    d = tmp_path / "handover"
    d.mkdir()
    (d / "implementer.md").write_text("# Handover — implementer\nUpdated: 2026-09-21\n")
    (d / "planner.md").write_text("# Handover — planner\nUpdated: 2026-09-21\n")

    context = build_additional_context(d)

    assert "implementer.md" in context
    assert "Handover — implementer" in context
    assert "planner.md" in context
    assert "docs/guides/agent_session_reset_boundaries.md" in context


def test_build_additional_context_falls_back_to_filename_for_blank_file(tmp_path):
    d = tmp_path / "handover"
    d.mkdir()
    (d / "empty-role.md").write_text("")
    context = build_additional_context(d)
    assert "empty-role" in context


def test_hook_prints_nothing_for_non_clear_source(tmp_path):
    handover = tmp_path / ".claude" / "handover"
    handover.mkdir(parents=True)
    (handover / "implementer.md").write_text("# Handover — implementer\n")

    out = _run_hook({"source": "startup"}, cwd=tmp_path)
    assert out.strip() == ""


def test_hook_prints_nothing_when_no_handover_notes_exist(tmp_path):
    out = _run_hook({"source": "clear"}, cwd=tmp_path)
    assert out.strip() == ""


def test_hook_prints_additional_context_json_on_clear_with_notes(tmp_path):
    handover = tmp_path / ".claude" / "handover"
    handover.mkdir(parents=True)
    (handover / "implementer.md").write_text("# Handover — implementer\n")

    out = _run_hook({"source": "clear"}, cwd=tmp_path)
    assert out.strip() != ""
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "implementer.md" in payload["hookSpecificOutput"]["additionalContext"]


def test_hook_fails_open_on_malformed_stdin(tmp_path):
    result = subprocess.run(
        [sys.executable, str(_HOOK_SCRIPT)],
        input="not valid json", capture_output=True, text=True, cwd=str(tmp_path), timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
