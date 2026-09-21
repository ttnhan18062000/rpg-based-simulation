#!/usr/bin/env python3
"""SessionStart hook: on a `/clear` (stdin `source == "clear"`), lists `.claude/handover/*.md`
file paths and first-line titles as `additionalContext` — never the note bodies themselves, so the
per-clear cost stays small no matter how many roles have a note. TCK-20260921-SESSION-CONTEXT-
RESET-TRIAL.

Keyed by role name, not `cwd` — several sessions share the main checkout (the same hazard shape as
the confirmed `.claude/current_run` sidecar contamination), so one note per role, not per
directory. See `docs/guides/agent_session_reset_boundaries.md` for the handover note format and
the reset-boundary map this hook exists to make reachable at the one moment it matters.

Read-only, fails open: prints nothing and exits 0 on any error, an unrecognized `source`, a
missing directory, or an empty directory. Never treats "hook input didn't parse" as reportable.
"""
import json
import sys
from pathlib import Path

HANDOVER_DIR = Path(".claude/handover")


def _first_line_title(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    return line.lstrip("#").strip()
    except OSError:
        pass
    return path.stem


def build_additional_context(handover_dir: Path) -> str:
    """Pure logic, no stdin — the part tests exercise directly."""
    if not handover_dir.is_dir():
        return ""
    notes = sorted(handover_dir.glob("*.md"))
    if not notes:
        return ""
    lines = ["session-reset-handover: existing handover notes found —"]
    for note in notes:
        lines.append(f"  {note} — {_first_line_title(note)}")
    lines.append(
        "Read the one matching your role before starting; see "
        "docs/guides/agent_session_reset_boundaries.md for the format."
    )
    return "\n".join(lines)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    if payload.get("source") != "clear":
        return 0

    context = build_additional_context(HANDOVER_DIR)
    if not context:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
