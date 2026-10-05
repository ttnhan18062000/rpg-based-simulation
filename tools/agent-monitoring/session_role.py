"""tools/agent-monitoring/session_role.py: the resolved session-layer role of a monitoring writer
(TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT; plan docs/plans/agent_infrastructure/
session_layer_working_process.md section 11).

`session_role` is read from the per-session binding record that SessionStart writes (tools/sessions/state.py)
by SESSION ID, so a session resumed outside the launcher is still attributed and two concurrent sessions never
swap roles. It is never read from the shared unscoped `.claude/current_run` (the cross-session contamination
ticket) and it is a separate field from `agent`: the `agent` vocabulary and its drift ratchet are untouched.
`unresolved` means no binding names the session (a plain `claude` session, or no session id at all).
Never raises.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

UNRESOLVED = "unresolved"
_REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_session_role(session_id: str | None = None, cwd: str | None = None) -> str:
    """The role instance bound to `session_id` (default: `CLAUDE_CODE_SESSION_ID`), else `unresolved`."""
    try:
        sid = session_id if session_id is not None else os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        if not sid:
            return UNRESOLVED
        if str(_REPO_ROOT) not in sys.path:
            sys.path.append(str(_REPO_ROOT))
        from tools.sessions import state as st
        from tools.sessions.guard import find_session_instance

        return find_session_instance(st.state_root(cwd or "."), sid) or UNRESOLVED
    except Exception:  # noqa: BLE001 - monitoring must never fail because attribution failed
        return UNRESOLVED


def stamp(record: dict, session_id: str | None = None) -> dict:
    """`record` with `session_role` added unless the caller already supplied one. Never mutates the input."""
    if "session_role" in record:
        return record
    return {**record, "session_role": resolve_session_role(session_id)}
