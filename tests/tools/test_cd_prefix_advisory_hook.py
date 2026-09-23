"""Tests for tools/agent-monitoring/cd_prefix_advisory_hook.py.

Batch B ticket 2 of 3 (context/token cost reduction). Mirrors write_path_guard.py's design: a
pure, directly-testable detection function plus a thin stdin-JSON CLI wrapper, tested separately
(inline unit tests for the pure function, subprocess tests for the CLI's fail-open and
hookSpecificOutput shape).
"""
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "cd_prefix_advisory_hook.py"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from cd_prefix_advisory_hook import detect_redundant_cd_prefix  # noqa: E402


# ---------------------------------------------------------------------------
# detect_redundant_cd_prefix — normal flow: the exact redundant case
# ---------------------------------------------------------------------------

def test_flags_cd_into_the_exact_current_directory():
    msg = detect_redundant_cd_prefix(
        "cd /home/u24desktop/Working/repo && git status", "/home/u24desktop/Working/repo",
    )
    assert msg is not None
    assert "cd-prefix" in msg


def test_flags_cd_with_trailing_slash_normalized():
    msg = detect_redundant_cd_prefix(
        "cd /home/u24desktop/Working/repo/ && ls", "/home/u24desktop/Working/repo",
    )
    assert msg is not None


def test_flags_quoted_cd_target():
    msg = detect_redundant_cd_prefix(
        "cd '/home/u24desktop/Working/repo' && pytest tests/", "/home/u24desktop/Working/repo",
    )
    assert msg is not None


def test_flags_relative_dot_target_matching_current_dir():
    msg = detect_redundant_cd_prefix("cd . && git diff", "/home/u24desktop/Working/repo")
    assert msg is not None


def test_flags_newline_separated_cd_the_dominant_real_shape():
    """TCK-20260923-CD-PREFIX-SEPARATOR-REACH-FIX: a real-corpus reach check found newline is the
    dominant separator in this corpus (47.7% of all cd-headed calls vs. under 2.4% for &&/;
    combined) -- the original &&-only pattern missed 97.7% of the population it targeted. This is
    the shape that must never regress again."""
    msg = detect_redundant_cd_prefix(
        "cd /home/u24desktop/Working/repo\npython3 -c \"print(1)\"",
        "/home/u24desktop/Working/repo",
    )
    assert msg is not None


def test_flags_semicolon_separated_cd():
    msg = detect_redundant_cd_prefix(
        "cd /home/u24desktop/Working/repo; pytest tests/", "/home/u24desktop/Working/repo",
    )
    assert msg is not None


# ---------------------------------------------------------------------------
# detect_redundant_cd_prefix — must NOT flag a genuine directory switch
# ---------------------------------------------------------------------------

def test_does_not_flag_cd_into_a_different_directory():
    msg = detect_redundant_cd_prefix(
        "cd /home/u24desktop/Working/other-repo && git status", "/home/u24desktop/Working/repo",
    )
    assert msg is None


def test_does_not_flag_newline_separated_cd_into_a_different_directory():
    msg = detect_redundant_cd_prefix(
        "cd /home/u24desktop/Working/other-repo\npython3 -c \"print(1)\"",
        "/home/u24desktop/Working/repo",
    )
    assert msg is None


def test_does_not_flag_cd_into_a_subdirectory():
    msg = detect_redundant_cd_prefix(
        "cd /home/u24desktop/Working/repo/subdir && ls", "/home/u24desktop/Working/repo",
    )
    assert msg is None


def test_does_not_flag_cd_into_a_worktree():
    msg = detect_redundant_cd_prefix(
        "cd /home/u24desktop/Working/repo/.claude/worktrees/other-ticket && git log",
        "/home/u24desktop/Working/repo",
    )
    assert msg is None


# ---------------------------------------------------------------------------
# detect_redundant_cd_prefix — edge cases / non-matches
# ---------------------------------------------------------------------------

def test_does_not_flag_command_with_no_cd_prefix():
    assert detect_redundant_cd_prefix("git status", "/home/u24desktop/Working/repo") is None


def test_does_not_flag_bare_cd_with_no_chained_command():
    assert detect_redundant_cd_prefix("cd /home/u24desktop/Working/repo", "/home/u24desktop/Working/repo") is None


def test_does_not_flag_cd_that_is_not_the_leading_token():
    msg = detect_redundant_cd_prefix(
        "echo hi && cd /home/u24desktop/Working/repo && ls", "/home/u24desktop/Working/repo",
    )
    assert msg is None


def test_empty_command_does_not_crash():
    assert detect_redundant_cd_prefix("", "/home/u24desktop/Working/repo") is None


def test_handles_tilde_expansion():
    import os
    home = os.path.expanduser("~")
    msg = detect_redundant_cd_prefix("cd ~ && ls", home)
    assert msg is not None


# ---------------------------------------------------------------------------
# CLI wrapper — stdin JSON in, hookSpecificOutput JSON out, fail-open on bad input
# ---------------------------------------------------------------------------

def _run_cli(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_MODULE_PATH)],
        input=json.dumps(payload), capture_output=True, text=True,
    )


def test_cli_emits_hook_specific_output_for_redundant_cd():
    result = _run_cli({
        "tool_input": {"command": "cd /a/b && git status"},
        "cwd": "/a/b",
    })
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert "cd-prefix" in out["hookSpecificOutput"]["additionalContext"]


def test_cli_prints_nothing_for_non_matching_command():
    result = _run_cli({"tool_input": {"command": "git status"}, "cwd": "/a/b"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_cli_fails_open_on_malformed_stdin():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], input="not valid json",
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""
