"""Resolve which role a SessionStart belongs to, from the harness signals alone (pure; no I/O).

Plan section 5, "Binding", and the M0o precedence table (observed 2026-10-03, Claude Code 2.1.286):

    signal         start  resume (no flags)                     fork      PreToolUse
    session_title  yes    yes (kept in the transcript)          yes       no
    agent_type     yes    SessionStart: ABSENT                  not probed yes, with --agent
    SESSION_ROLE   yes    no (per-process, not persisted)       not probed not probed

So on `source == "resume"` neither `agent_type` nor the environment is trusted: the title is the resume
signal. On every other source the three signals are compared; if they name different roles nothing is
resolved ("disagree"), and if none names a role nothing is resolved ("unresolved"). The hook never guesses.
The worktree path is NOT an identity signal (several roles share one worktree); it is recorded, not used.

A role with `max_sessions: N` may run N instances; the second and later are named `<role>-2` .. `<role>-N` and
get their own role-state directory, keyed by that INSTANCE id. `Resolution.role` is always the manifest role;
`Resolution.instance` is the instance id (the role id itself for the first). `agent_type` names the card, which
is shared, so it never selects an instance beyond the first; a title or environment value of `<role>-N` does.

A signal counts only if it names a role in the manifest: an unknown title (a human-chosen session name) is
ignored, not a disagreement. `/clear` and live rename are unprobed (class 2); the design assumes only that
at least one signal survives start, resume and fork.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.sessions.roster import Roster

AGENT_PREFIX = "session-"
RESOLVED, UNRESOLVED, DISAGREE = "resolved", "unresolved", "disagree"


@dataclass(frozen=True)
class Signals:
    source: str
    agent_type: str | None = None
    session_title: str | None = None
    env_role: str | None = None


@dataclass(frozen=True)
class Resolution:
    status: str  # RESOLVED | UNRESOLVED | DISAGREE
    role: str | None
    used: tuple[tuple[str, str], ...]  # (signal name, instance it named), the evidence for the binding record
    reason: str
    instance: str | None = None


def instance_ids(role_id: str, max_sessions: int) -> tuple[str, ...]:
    return (role_id,) + tuple(f"{role_id}-{n}" for n in range(2, max_sessions + 1))


def _names(roster: Roster) -> dict[str, tuple[str, str] | None]:
    """name -> (role id, instance id), over role ids, session names, legacy names and `<role>-N` instance ids;
    None marks an ambiguous name."""
    table: dict[str, tuple[str, str] | None] = {}

    def add(name: str, role: str, instance: str) -> None:
        table[name] = (role, instance) if table.get(name, (role, instance)) == (role, instance) else None

    for r in roster.roles:
        for name in {r.role, r.session_name, r.legacy_session_name} - {None}:
            add(name, r.role, r.role)
        for inst in instance_ids(r.role, r.max_sessions)[1:]:
            add(inst, r.role, inst)
    return table


def _lookup(name: str | None, table: dict, prefix: str = "") -> tuple[str, str] | None:
    if not name:
        return None
    if prefix and name.startswith(prefix):
        name = name[len(prefix):]
    return table.get(name)


def resolve(signals: Signals, roster: Roster) -> Resolution:
    table = _names(roster)
    named: list[tuple[str, tuple[str, str]]] = []
    for sig, value, prefix, trusted in (
        ("session_title", signals.session_title, "", True),
        ("agent_type", signals.agent_type, AGENT_PREFIX, signals.source != "resume"),
        ("env_role", signals.env_role, "", signals.source != "resume"),
    ):
        hit = _lookup(value, table, prefix) if trusted else None
        if hit:
            named.append((sig, hit))
    used = tuple((sig, inst) for sig, (_, inst) in named)
    roles = {role for _, (role, _) in named}
    if not roles:
        why = "resume: only the session title can resolve a role" if signals.source == "resume" else "no signal names a role"
        return Resolution(UNRESOLVED, None, (), why)
    if len(roles) > 1:
        return Resolution(DISAGREE, None, used, "signals name different roles: " + ", ".join(f"{s}={i}" for s, i in used))
    role = roles.pop()
    # agent_type only names the shared card (the first instance); a title/env `<role>-N` is more specific
    specific = {inst for sig, (_, inst) in named if sig != "agent_type"} - {role}
    if len(specific) > 1:
        return Resolution(DISAGREE, None, used, "signals name different instances of one role: " + ", ".join(sorted(specific)))
    instance = specific.pop() if specific else role
    return Resolution(RESOLVED, role, used, "resolved from " + ", ".join(s for s, _ in used), instance)
