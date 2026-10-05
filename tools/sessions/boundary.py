#!/usr/bin/env python3
"""Advisory `role_boundary` events: semantic boundaries are warned about and logged, never denied.

TCK-20261004-SESSION-LAYER-M5C-READ-ONLY-ALLOWLISTS-AND-ROLE-BOUNDARY-EVENTS. Plan:
docs/plans/agent_infrastructure/session_layer_working_process.md sections 9.0 and 10 ("Semantic and
organisational boundaries: advisory first"). `guard.py` calls `advise()` for a tool call it has already let
through, so this module never produces a permission decision and shares none of the guard's deny/ask set.

Two kinds, both for a RESOLVED role only (an unresolved plain session is not role-governed in v1):
  - `edit_outside_owns`: an Edit/Write/MultiEdit/NotebookEdit whose path another domain owns (per
    `route.route(path, from_domain=<caller's domain>)`) and the caller's role neither writes (`may_write`) nor
    owns (`owns`). An unowned path is not an event: no domain's claim is crossed.
  - `message_class_mismatch`: a SendMessage whose first line names a work-assigning class (dispatch, handoff,
    request) to a role whose `accepts_dispatch_from` does not list the sender (plan 9.0).

Each (kind, path class or target) warns once per session: the warning is the hook's `additionalContext`, the
event is one line in `agent-working/agent-monitoring/data/<iso-week>/role_boundary.jsonl`. The event carries role,
session id, kind, path or target, never message content, and has its own field set (never the `agent` field).
Every failure is swallowed: a write error or a bad roster must not fail or slow the tool call.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
MESSAGE_TOOL = "SendMessage"
KIND_EDIT = "edit_outside_owns"
KIND_MESSAGE = "message_class_mismatch"
_ASSIGNING_CLASS = re.compile(r"^\W*(dispatch|handoff|hand-off|request)\b", re.IGNORECASE)
_SEEN_DIR = "_boundary"


def find_worktree_root(cwd: str) -> Path | None:
    """The nearest ancestor holding `.git` (a directory, or the file a linked worktree has). Pure path walk, no git."""
    start = Path(cwd or ".").resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def repo_relative(file_path: str, cwd: str) -> str | None:
    """`file_path` relative to the worktree root, or None when it lies outside the worktree."""
    root = find_worktree_root(cwd)
    if root is None or not file_path:
        return None
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(cwd or ".").resolve() / path
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return None


def _path_class(domains: tuple[str, ...], rel: str) -> str:
    return f"{'+'.join(domains) or 'unowned'}:{'/'.join(rel.split('/')[:2])}"


def check_edit(payload: dict, role, roster):
    """`(kind, path_class, fields)` for an edit crossing another domain's claim, else None. Pure."""
    from tools.sessions.route import OWNED, SPLIT, _matches, route

    tool_input = payload.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    rel = repo_relative(str(raw), str(payload.get("cwd") or "."))
    if rel is None:
        return None
    # `may_write: ["**"]` (every implementer) says nothing about which domain a path belongs to, so it never exempts
    granted = (*(g for g in role.may_write if g != "**"), *role.owns)
    if any(_matches(g, rel) for g in granted):
        return None
    result = route(rel, roster, from_domain=role.domain)
    if result.status not in (OWNED, SPLIT) or role.domain in result.domains:
        return None
    return KIND_EDIT, _path_class(result.domains, rel), {
        "path": rel, "owner_domains": list(result.domains), "owner_seats": list(result.seats),
    }


def _base_role(instance: str, roster):
    if roster.role(instance):
        return roster.role(instance)
    head, _, tail = instance.rpartition("-")
    return roster.role(head) if tail.isdigit() else None


def check_message(payload: dict, instance: str, roster):
    """`(kind, target, fields)` for a work-assigning message to a role that does not accept it from this sender."""
    tool_input = payload.get("tool_input") or {}
    message = tool_input.get("message")
    if not isinstance(message, str):
        return None
    first_line = message.lstrip().split("\n", 1)[0]
    match = _ASSIGNING_CLASS.match(first_line)
    if not match:
        return None
    target = str(tool_input.get("to") or "")
    receiver = next((r for r in roster.roles if target in (r.role, r.session_name)), None)
    if receiver is None:
        return None
    sender = _base_role(instance, roster)
    sender_ids = {instance, sender.role if sender else ""}
    if sender_ids & set(receiver.accepts_dispatch_from):
        return None
    return KIND_MESSAGE, receiver.role, {
        "target": receiver.role, "message_class": match.group(1).lower(),
        "accepts_dispatch_from": list(receiver.accepts_dispatch_from),
    }


def _seen_path(root: Path, session_id: str) -> Path:
    return root / _SEEN_DIR / f"{re.sub(r'[^A-Za-z0-9._-]', '_', session_id)}.json"


def first_time(root: Path, session_id: str, key: str) -> bool:
    """True once per (session, key); a state write failure returns False so a failure never repeats a warning."""
    try:
        path = _seen_path(root, session_id)
        seen = set(json.loads(path.read_text())) if path.exists() else set()
        if key in seen:
            return False
        seen.add(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sorted(seen)))
        return True
    except Exception:  # noqa: BLE001 - advisory: never fail, never spam
        return False


def write_event(record: dict, data_dir: Path | None = None) -> bool:
    """Append one record to this week's role_boundary.jsonl through the shared locked writer. Never raises."""
    try:
        sys.path.insert(0, str(_REPO_ROOT / "tools" / "agent-monitoring"))
        from writer import write_line

        from tools.agent_working_paths import AGENT_MONITORING

        now = datetime.now(timezone.utc)
        base = Path(data_dir) if data_dir is not None else Path(AGENT_MONITORING) / "data"
        target = base / now.strftime("%G-W%V") / "role_boundary.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        return bool(write_line(target, json.dumps(record, separators=(",", ":"))))
    except Exception:  # noqa: BLE001
        return False


def _warning(kind: str, fields: dict, role_id: str) -> str:
    if kind == KIND_EDIT:
        owners = ", ".join(fields["owner_domains"])
        seats = ", ".join(fields["owner_seats"]) or "its planner"
        return (f"role-boundary advisory (not blocked): {role_id} is editing {fields['path']}, which the {owners} "
                f"domain owns. Route it to {seats} unless this is a recorded exception.")
    accepted = ", ".join(fields["accepts_dispatch_from"]) or "nobody"
    return (f"role-boundary advisory (not blocked): {fields['message_class']} to {fields['target']}, which accepts "
            f"dispatch only from {accepted}. The receiver may treat it as fyi; send a question or finding, or go "
            "through its planner.")


def advise(payload: dict, caller, roster, root: Path, data_dir: Path | None = None) -> str | None:
    """The advisory text for this tool call (also logging the event), or None. Never raises."""
    try:
        tool = str(payload.get("tool_name", ""))
        if not caller.resolved or not caller.instance:
            return None
        role = roster.role(caller.role_id)
        if role is None:
            return None
        if tool in EDIT_TOOLS:
            found = check_edit(payload, role, roster)
        elif tool == MESSAGE_TOOL:
            found = check_message(payload, caller.instance, roster)
        else:
            return None
        if found is None:
            return None
        kind, key, fields = found
        session_id = str(payload.get("session_id") or "")
        if not first_time(root, session_id, f"{kind}|{key}"):
            return None
        write_event({
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event": "role_boundary", "kind": kind, "session_id": session_id or None,
            "session_role": caller.instance, "function": caller.function, "domain": role.domain,
            "tool": tool, **fields,
        }, data_dir)
        return _warning(kind, fields, caller.instance)
    except Exception:  # noqa: BLE001
        return None
