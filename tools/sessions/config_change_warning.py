#!/usr/bin/env python3
"""ConfigChange hook: warn the user when a settings or hook file changes under a running session.

TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION. Claude Code reloads settings and hooks while a session runs, so an
agent's edit to its own enforcement (`.claude/settings.json`, `.claude/settings.local.json`, a hook script) takes effect at
once (plan P-1b, R13). This hook cannot stop that and does not try: it prints a one-line warning to the user, naming
the source and the file, and exits 0. A warning is mistake reduction, not a boundary (plan section 10); it never blocks,
because blocking a legitimate owner edit would cost more than the warning saves.

Input (stdin JSON): `hook_event_name` "ConfigChange", `source` (user_settings, project_settings, local_settings,
policy_settings or skills) and `file_path`. Output: `{"systemMessage": "..."}` on stdout. Any problem exits 0 silently
(fail open: an advisory must never break a session).

WIRING: `test -f tools/sessions/config_change_warning.py || exit 0; python3 tools/sessions/config_change_warning.py`.
"""
from __future__ import annotations

import json
import sys


def warning(payload: dict) -> str:
    source = str(payload.get("source") or "unknown source")
    path = str(payload.get("file_path") or "an unknown file")
    return (
        f"Configuration changed while this session runs: {source} ({path}). Settings and hooks take effect immediately, "
        "including the rules that gate this session's own commands. If you did not expect this change, review it "
        "(git diff) before continuing."
    )


def main(stdin=None, stdout=None) -> int:
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    try:
        payload = json.loads(stdin.read())
        if not isinstance(payload, dict):
            return 0
        stdout.write(json.dumps({"systemMessage": warning(payload)}) + "\n")
    except Exception:  # noqa: BLE001 - an advisory never fails a session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
