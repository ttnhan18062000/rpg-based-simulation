#!/usr/bin/env python3
"""ConfigChange hook: tell the user, by a terminal notification, that a settings or skill file changed under a running session.

TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION. Claude Code reloads settings and hooks while a session runs, so an
agent's edit to its own enforcement (`.claude/settings.json`, `.claude/settings.local.json`, a skill file) takes effect
at once (plan P-1b, R13). This hook cannot stop that and does not try: a warning is mistake reduction, not a boundary
(plan section 10), and blocking a legitimate owner edit would cost more than the warning saves.

What reaches whom (code.claude.com/docs/en/hooks.md, "ConfigChange decision control" and "Emit terminal notifications"):
- ConfigChange discards `systemMessage` and `continue`, so a message in those fields reaches neither the user nor the agent.
  This hook does not use them.
- `terminalSequence` is a side-effect field. Claude Code writes it to the terminal itself, only in an interactive session
  while its interface is on screen, and ignores the whole field if it holds anything outside the allowlist (OSC 0/1/2/9/99/777
  and BEL). The docs do not name ConfigChange in the `terminalSequence` text: that it fires here is the general rule, not a
  stated promise. Whether it shows in a given terminal is for the owner's live test to settle.
- The agent is not told. Telling it would need new settings text.
- A local log line is written regardless, so a change leaves a trace even if no notification shows.

Input (stdin JSON): `hook_event_name` "ConfigChange", `source` (user_settings, project_settings, local_settings,
policy_settings or skills) and optionally `file_path`. Output: `{"terminalSequence": "..."}` on stdout, an OSC 9
notification, an OSC 777 notification and a bell, all control characters stripped from the values put into them. Log:
one JSON line per event in `<repo>/tmp/config_change.log` (gitignored): time, hook_event_name, source, file_path and the
sorted top-level key names of the event, nothing else from it. The log and the notification fail independently. Always
exits 0 and never blocks (fail open: an advisory must never break a session).

WIRING (the approved text, #715 6543054968): `R=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0; test -f
"$R/tools/sessions/config_change_warning.py" || exit 0; python3 "$R/tools/sessions/config_change_warning.py"`.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_LOG_ENV = "CONFIG_CHANGE_WARNING_LOG"
_DEFAULT_LOG = Path(__file__).resolve().parents[2] / "tmp" / "config_change.log"
_VALUE_CAP = 200
_ESC, _BEL = "\x1b", "\x07"


def _clean(value: object, fallback: str, cap: int = _VALUE_CAP) -> str:
    """The value as short printable text: control characters (ESC and BEL included) and `;` removed."""
    text = "".join(ch for ch in str(value) if ch.isprintable() and ch != ";") if value else ""
    return (text.strip() or fallback)[:cap]


def sequence(payload: dict) -> str:
    """OSC 9 and OSC 777 notifications plus a bell: only allowlisted sequences, so the field is never ignored for content."""
    where = f"{_clean(payload.get('source'), 'unknown source', 40)}: {_clean(payload.get('file_path'), 'an unknown file', 80)}"
    body = f"Config changed under a running session ({where}). Review with git diff."
    return f"{_ESC}]9;{body}{_BEL}{_ESC}]777;notify;Claude Code config changed;{body}{_BEL}{_BEL}"


def log_line(payload: dict, now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return json.dumps(
        {
            "time": stamp,
            "hook_event_name": _clean(payload.get("hook_event_name"), "", 40),
            "source": _clean(payload.get("source"), "", 40),
            "file_path": _clean(payload.get("file_path"), "", 300),
            "keys": sorted(_clean(key, "?", 60) for key in payload),
        },
        sort_keys=True,
    )


def _append_log(payload: dict, log_path: Path | None) -> None:
    path = log_path or Path(os.environ.get(_LOG_ENV) or _DEFAULT_LOG)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(log_line(payload) + "\n")


def main(stdin=None, stdout=None, log_path: Path | None = None) -> int:
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    try:
        payload = json.loads(stdin.read())
    except Exception:  # noqa: BLE001 - an advisory never fails a session
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        _append_log(payload, log_path)
    except Exception:  # noqa: BLE001 - a log failure must not stop the notification
        pass
    try:
        stdout.write(json.dumps({"terminalSequence": sequence(payload)}) + "\n")
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
