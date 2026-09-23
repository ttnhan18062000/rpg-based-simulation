#!/usr/bin/env python3
"""Advisory-only PreToolUse hook for Bash: nudges against a redundant `cd <path> && ...` prefix
(TCK to be filed — Batch B ticket 2 of 3, context/token cost reduction).

Measured driver (`tools/agent-monitoring/bash_command_mix.py`, ticket 1 of this batch): `cd` is
the single largest Bash command head at ~21-22% of all Bash calls over W30-W39 — almost entirely
`cd <path> && ...` prefixes in a harness where the Bash tool's own working directory already
persists between calls (this repo's own system prompt: "The working directory persists between
Bash calls, but shell state does not... never prepend cd <current-directory> to a git command").

Detects exactly one narrow, provably-redundant case: the command's `cd` target normalizes to the
SAME directory the Bash call is about to start from. This is a real false-positive risk if done
loosely (a `cd` into a genuinely different directory — a worktree switch, a subproject — is
legitimate and must never be flagged), so `detect_redundant_cd_prefix()` only fires on exact
normalized-path equality, never on a heuristic "looks like a repo path" match.

Advisory only, per this repo's standing proportionate-checks rule
(`[[feedback_agent_tooling_checks_proportionate]]`) and this batch's own explicit constraint: no
hook here may fail or block a Bash call. Mirrors the existing sidecar-check hook's shape (a
PreToolUse `additionalContext` nudge, never a decision/block field) and `tools/write_path_guard.py`
::scan_for_secrets's existing secret-scan hook wiring (pure function + thin stdin-JSON CLI wrapper,
wrapped in try/except so a hook failure never blocks the tool call it's advising on).
"""
from __future__ import annotations

import json
import os
import re
import sys

_CD_PREFIX_PATTERN = re.compile(r"^\s*cd\s+(\S+)\s*&&")


def detect_redundant_cd_prefix(command: str, current_dir: str) -> "str | None":
    """Returns an advisory message if `command` opens with `cd <path> &&` where `<path>`
    normalizes to the exact same directory as `current_dir` (the Bash call's own starting
    directory) -- a provably redundant prefix. Returns None for every other case, including a
    `cd` into any different directory, which may be a genuine, legitimate need (switching
    worktrees, entering a subproject) and must never be second-guessed by this heuristic."""
    match = _CD_PREFIX_PATTERN.match(command)
    if not match:
        return None

    raw_target = match.group(1).strip("'\"")
    target = os.path.expanduser(raw_target)
    if not os.path.isabs(target):
        target = os.path.join(current_dir, target)
    target = os.path.normpath(target)
    current = os.path.normpath(current_dir)

    if target != current:
        return None

    return (
        "cd-prefix: this command's `cd <path> &&` prefix targets the directory this Bash call "
        "already starts in — the working directory persists between calls in this harness, so "
        "the prefix is likely redundant. Advisory only, not blocked; a cd into a genuinely "
        "different directory is unaffected by this check."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", payload).get("command", "")
        current_dir = payload.get("cwd") or os.getcwd()
        message = detect_redundant_cd_prefix(command, current_dir)
        if message:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": message,
                }
            }))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
