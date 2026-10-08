#!/usr/bin/env python3
"""Advisory PreToolUse(Bash) hook: remind to call search_docs before reading `src/` or `docs/`
(TCK-20261008-CONTEXT-SEARCH-HOOK-NARROWING; replaces the inline shell hook in `.claude/settings.json`).

CLAUDE.md requires `mcp__knowledge-search__search_docs` (then `graphify query`) before grep or raw file reads.
The inline hook fired on any Bash command containing `grep`, `rg `, `find `, ... even a `git commit` message that
mentioned one, so its reminder carried no information. This one speaks only when BOTH hold:

1. the command is an investigation READ (grep/rg/find/cat/head/tail/sed -n/... as a command word) whose target path
   is under `src/` or `docs/` (writes, heredoc bodies and `>` redirect targets do not count), and
2. this session has not yet called `search_docs` (read from the session transcript, found once then cached in a
   sentinel file so later calls are one `stat`). If the transcript cannot be read, it stays silent: fail open.

Advisory only: it never blocks, never writes a decision field, and exits 0 on every path including any exception.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

READ_COMMANDS = frozenset({"grep", "egrep", "fgrep", "rg", "ripgrep", "find", "fd", "ack", "ag", "cat", "head", "tail",
                           "less", "more", "bat", "sed", "awk"})
SEARCH_PATTERNS = (re.compile(rb'"name"\s*:\s*"mcp__knowledge-search__search_docs"'), re.compile(rb"knowledge_search\.py query"))
MESSAGE = ("context-search: this reads src/ or docs/ and search_docs (mcp__knowledge-search__search_docs) has not been "
           "called in this session. CLAUDE.md requires search_docs first, then graphify query, before grep or raw file "
           "reads; grep and file reads are follow-ups to what those return.")
_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?(?:\n\1\b|\Z)", re.S)
_REDIRECT = re.compile(r"\d?>>?\s*\S+")
_SPLIT = re.compile(r"\|\||&&|[|;\n(){}]")
_ENV_ASSIGN = re.compile(r"^\w+=\S*$")
_TARGET = re.compile(r"^(?:\./)?(?:src|docs)(?:/|$)")


def _is_target(token: str) -> bool:
    token = token.strip("'\"")
    if _TARGET.match(token):
        return True
    return token.startswith("/") and "/rpg-based-simulation/" in token and bool(re.search(r"/(?:src|docs)(?:/|$)", token))


def is_investigation_read(command: str) -> bool:
    """True when some segment of `command` is a read command with a target under src/ or docs/."""
    text = _REDIRECT.sub(" ", _HEREDOC.sub(" ", command or ""))
    for segment in _SPLIT.split(text):
        words = segment.split()
        while words and _ENV_ASSIGN.match(words[0]):
            words = words[1:]
        if not words or os.path.basename(words[0]) not in READ_COMMANDS:
            continue
        if words[0] == "sed" and "-n" not in words[1:]:
            continue
        if any(_is_target(w) for w in words[1:]):
            return True
    return False


def _sentinel(session_id: str) -> Path:
    safe = re.sub(r"[^\w.-]", "_", session_id)[:80]
    return Path(os.environ.get("TMPDIR") or tempfile.gettempdir()) / f"context_search_hook_{safe}"


def search_docs_called(payload: dict) -> bool | None:
    """True/False from the session transcript (a tool_use of search_docs, or the CLI fallback); None when it cannot
    be told (no transcript path, unreadable): the caller then stays silent."""
    session_id = str(payload.get("session_id") or "")
    if session_id and _sentinel(session_id).exists():
        return True
    path = payload.get("transcript_path")
    if not path or not os.path.isfile(path):
        return None
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    for pattern in SEARCH_PATTERNS:
        for match in pattern.finditer(data):
            line_start = data.rfind(b"\n", 0, match.start()) + 1
            line_end = data.find(b"\n", match.end())
            line = data[line_start: line_end if line_end != -1 else len(data)]
            if re.search(rb'"type"\s*:\s*"tool_use"', line):
                if session_id:
                    try:
                        _sentinel(session_id).write_text("1")
                    except OSError:
                        pass
                return True
    return False


def decide(payload: dict) -> str | None:
    """The reminder text, or None for silence."""
    command = str((payload.get("tool_input") or {}).get("command") or "")
    if not is_investigation_read(command):
        return None
    return MESSAGE if search_docs_called(payload) is False else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        message = decide(payload)
        if message:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": message}}))
    except Exception:  # noqa: BLE001 - advisory: any failure is silence, never a blocked tool call
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
