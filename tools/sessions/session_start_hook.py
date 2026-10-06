#!/usr/bin/env python3
"""Role-aware SessionStart hook (plan section 5, "Binding"; TCK-20261004-SESSION-LAYER-M2B).

On `startup`, `resume`, `clear` and `compact` it gathers the harness signals, resolves the role
(`tools/sessions/resolve.py`), binds the current `session_id` to it (a binding record plus `instance.json`
via `tools/sessions/state.py`), takes the writer lease when the role is its worktree's writer, and injects
that role's card and ONLY that role's handover note. It never injects another role's title or note.

A session that resolves no role (a plain `claude`, or signals that disagree) gets nothing privileged: the old
all-roles handover listing (`tools/agent-monitoring/session_start_handover_hook.py`, kept as the fallback by
owner decision 2026-10-04) plus one line saying how to launch with a role. A transit-bundle notice rides on
every outcome.

This is a context hook, not an authority one: it FAILS OPEN. Any exception, an unparseable payload, an
unreadable manifest or an unknown `source` prints nothing and exits 0. The transcript path is stored as a hint
only; nothing here depends on it (M0p: after a cross-cwd resume it points into the new cwd's project dir).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / "tools" / "agent-monitoring")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SOURCES = ("startup", "resume", "clear", "compact")
HANDOVER_CAP_CHARS = 8000
LAUNCH_HINT = (
    "session-roles: no role resolved for this session (plain `claude`, or its signals disagree), so nothing "
    "role-specific is injected. Launch with a role to get your card and handover: "
    "`claude --name <role-id> --agent session-<role-id>` (roles: registries/session_roles.yaml)."
)


def _git(cwd: str, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10)
    return out.stdout.strip() if out.returncode == 0 else ""


def _same_process(recorded, current) -> bool:
    """True when both are known and name the same process (same pid AND start time; the command line is not compared)."""
    return recorded is not None and current is not None and (recorded.pid, recorded.start) == (current.pid, current.start)


def find_claude_pid(environ=os.environ, proc_root: Path = Path("/proc")) -> int | None:
    """`CLAUDE_PID` when the launcher or harness supplies it, else the nearest ancestor that looks like claude."""
    from tools.sessions.state import process_identity

    raw = environ.get("CLAUDE_PID", "")
    if raw.isdigit() and process_identity(int(raw), proc_root):
        return int(raw)
    pid = os.getppid()
    for _ in range(8):
        ident = process_identity(pid, proc_root)
        if ident is None:
            return None
        if Path(ident.cmdline.split(" ")[0]).name.startswith("claude"):
            return pid
        try:
            pid = int((proc_root / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            return None
        if pid <= 1:
            return None
    return None


def _handover_text(role, root: Path) -> str:
    path = root / role.handover
    if not path.is_file():
        return f"(no handover note yet at {role.handover}; create one at the first HARD reset boundary)"
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) > HANDOVER_CAP_CHARS:
        text = text[:HANDOVER_CAP_CHARS] + f"\n[... note cut at {HANDOVER_CAP_CHARS} chars; full file: {role.handover}]"
    return f"Your handover note ({role.handover}):\n{text}"


def bind(payload: dict, environ, root: Path, state_root: Path, proc_root: Path = Path("/proc")) -> str:
    """Resolve, bind and compose the injected context. Returns "" when nothing should be injected."""
    from tools.sessions import manifest_diff as md
    from tools.sessions import state as st
    from tools.sessions.card import compose_card
    from tools.sessions.resolve import RESOLVED, Signals, resolve
    from tools.sessions.roster import load_authority, load_roster

    source = payload.get("source")
    roster, authority = load_roster(root), load_authority(root)
    res = resolve(Signals(source=source, agent_type=payload.get("agent_type"),
                          session_title=payload.get("session_title"), env_role=environ.get("SESSION_ROLE")), roster)
    if res.status != RESOLVED:
        return ""  # the caller adds the fallback listing and the launch hint
    role = roster.role(res.role)
    instance_id = res.instance or role.role
    cwd = payload.get("cwd") or os.getcwd()
    worktree = str(Path(_git(cwd, "rev-parse", "--show-toplevel") or cwd).resolve())
    digest = md.manifest_digest(root)
    proc = None
    pid = find_claude_pid(environ, proc_root)
    if pid is not None:
        proc = st.process_identity(pid, proc_root)

    previous = st.read_bindings(state_root, instance_id)
    prior_snapshot = st.read_role_file(state_root, instance_id, "manifest.json")
    prior_instance = st.read_instance(state_root, instance_id)

    binding = st.Binding(
        session_id=str(payload.get("session_id", "")), role=instance_id, source=str(source), worktree=worktree,
        branch=_git(cwd, "rev-parse", "--abbrev-ref", "HEAD"), transcript_path=str(payload.get("transcript_path", "")),
        process=proc, manifest_digest=digest, ts=st._now(),
    )
    st.record_start(state_root, binding)
    snap = md.snapshot(role.role, roster, authority)
    st.write_role_file(state_root, instance_id, "manifest.json", snap.to_json())

    parts = [compose_card(role.role, roster, authority, root)]
    if instance_id != role.role:
        parts.append(f"session-roles: you are instance `{instance_id}` of role `{role.role}` (a second holder; the first is `{role.role}`).")
    notes: list[str] = []

    # TCK-20261006-SESSION-START-CLEAR-FALSE-LIVE-HOLDER-WARNING: a `/clear` gives the SAME process a new session id, so the prior holder
    # recorded in this very process is this session's own superseded predecessor, not a second writer.
    if prior_instance is not None and not prior_instance.released and prior_instance.holder.session_id != binding.session_id \
            and not _same_process(prior_instance.holder.process, proc) and st.liveness(prior_instance, proc_root) == st.LIVE:
        notes.append(f"session-roles: another LIVE instance already holds role `{instance_id}` "
                     f"(session {prior_instance.holder.session_id}); two writers on one role is not supported.")
    if source in ("resume", "clear") and previous and previous[-1].manifest_digest != digest and prior_snapshot:
        try:
            change = md.diff(md.Snapshot.from_json(prior_snapshot), snap)
        except ValueError:
            change = None
        if change and change.lines:
            notes.append("session-roles: the manifest changed since your last binding: " + " | ".join(change.lines))
            if change.authority_reduced:
                notes.append("session-roles: AUTHORITY WAS REDUCED. Re-evaluate before any privileged action; "
                             "text already in your context may still describe the old, wider authority.")
        elif change is None:
            notes.append("session-roles: the manifest changed since your last binding (previous summary unreadable).")

    wt = next((w for w in roster.worktrees if w.name == role.worktree), None)
    if wt is not None and wt.writer == role.role:
        try:
            st.take_lease(state_root, worktree, instance_id, binding.session_id, proc, proc_root)
        except st.LeaseRefused as exc:
            notes.append(f"session-roles: WRITER LEASE NOT TAKEN: {exc}")
    parts.extend(notes)
    parts.append(_handover_text(role, root))
    return "\n\n".join(parts)


def build_context(payload: dict, environ=os.environ, root: Path = _REPO_ROOT, state_root: Path | None = None,
                  proc_root: Path = Path("/proc")) -> str:
    """The full additionalContext for a payload; "" for nothing. Raises on error (main() fails open)."""
    import session_start_handover_hook as old
    HANDOVER_DIR, build_additional_context = old.HANDOVER_DIR, old.build_additional_context
    # the transit notice lives in the old hook module (TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT); absent on a
    # tree that predates it, in which case there is simply no notice
    build_transit_notice = getattr(old, "build_transit_notice", lambda _root: "")
    from tools.sessions import state as st

    if payload.get("source") not in SOURCES:
        return ""
    state_root = state_root or st.state_root(payload.get("cwd") or ".")
    context = bind(payload, environ, root, state_root, proc_root)
    if not context:
        fallback = build_additional_context(root / HANDOVER_DIR) if payload.get("source") == "clear" else ""
        context = "\n".join(p for p in (fallback, LAUNCH_HINT) if p)
    notice = build_transit_notice(root / "agent-working" / "handover-transit")
    return "\n".join(p for p in (context, notice) if p)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        context = build_context(payload)
    except Exception:
        return 0
    if not context:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
