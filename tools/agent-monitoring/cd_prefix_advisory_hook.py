#!/usr/bin/env python3
"""Advisory-only PreToolUse hook for Bash: nudges against a redundant `cd <path>` prefix
(TCK-20260923-CD-PREFIX-ADVISORY-HOOK, amended by TCK-20260923-CD-PREFIX-SEPARATOR-REACH-FIX;
Batch B, context/token cost reduction).

Measured driver (`tools/agent-monitoring/bash_command_mix.py`, ticket 1 of this batch): `cd` is
the single largest Bash command head at ~21-22% of all Bash calls over W30-W39 — almost entirely
`cd <path>` prefixes in a harness where the Bash tool's own working directory already persists
between calls (this repo's own system prompt: "The working directory persists between Bash calls,
but shell state does not... never prepend cd <current-directory> to a git command"). The separator
between the `cd` and what follows is NOT reliably `&&`: a real-corpus reach check
(`TCK-20260923-CD-PREFIX-SEPARATOR-REACH-FIX`) found the dominant real shape in this corpus is a
newline (`cd <path>\\n<command>`, 47.7% of all cd-headed calls, `&&`/`;` combined under 2.4%) — the
original `&&`-only pattern matched only 2.3% of the population it targeted, silently missing the
form actually written 97.1% of the time.

Detects exactly one narrow, provably-redundant case: the command's `cd` target normalizes to the
SAME directory the Bash call is about to start from. This is a real false-positive risk if done
loosely (a `cd` into a genuinely different directory — a worktree switch, a subproject — is
legitimate and must never be flagged), so `detect_redundant_cd_prefix()` only fires on exact
normalized-path equality, never on a heuristic "looks like a repo path" match.

Advisory only, per this repo's standing rule that agent-tooling checks stay proportionate rather
than becoming strict blocking gates (`CLAUDE.md`'s Proactive Tool Use section; this rule is not
itself codified as a CLAUDE.md line item, but every hook in `.claude/settings.json` follows it in
practice) and this batch's own explicit constraint: no hook here may fail or block a Bash call.
Mirrors the existing sidecar-check hook's shape (a PreToolUse `additionalContext` nudge, never a
decision/block field) and `tools/write_path_guard.py`::scan_for_secrets's existing secret-scan hook
wiring (pure function + thin stdin-JSON CLI wrapper, wrapped in try/except so a hook failure never
blocks the tool call it's advising on).
"""
from __future__ import annotations

import json
import os
import re
import sys

_CD_PREFIX_PATTERN = re.compile(r"^\s*cd\s+(\S+)\s*(?:&&|;|\n)")


def detect_redundant_cd_prefix(command: str, current_dir: str) -> "str | None":
    """Returns an advisory message if `command` opens with `cd <path>` followed by `&&`, `;`, or
    a newline, where `<path>` normalizes to the exact same directory as `current_dir` (the Bash
    call's own starting directory) -- a provably redundant prefix. Returns None for every other
    case, including a `cd` into any different directory, which may be a genuine, legitimate need
    (switching worktrees, entering a subproject) and must never be second-guessed by this
    heuristic, and a bare `cd <path>` with nothing chained after it (a real, distinct 52% of this
    corpus's cd-headed calls, but not a *prefix* this hook is scoped to advise on)."""
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
        "cd-prefix: this command's leading `cd <path>` targets the directory this Bash call "
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
