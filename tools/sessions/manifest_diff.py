"""Manifest digest and the per-role snapshot used to say what changed between two bindings.

Plan section 5, "Manifest revision": a card carries the manifest digest; on resume or clear, if it differs
from the previous binding's, the hook says what changed in a line or two, and an authority REDUCTION is
flagged for explicit re-evaluation, because re-injecting a card cannot remove stale policy already in a
resumed context. A digest alone cannot say what changed, so the role's last-seen summary is kept beside its
runtime state (`manifest.json`, written atomically by `state.write_role_file`).

Authority reduction means: something newly forbidden, something newly needing the user, or a grant removed.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

from tools.sessions.roster import AUTHORITY_REL_PATH, REPO_ROOT, ROLES_REL_PATH, Authority, Roster


@dataclass(frozen=True)
class Snapshot:
    owns: tuple[str, ...]
    routes: tuple[str, ...]
    forbidden: tuple[str, ...]
    needs_user: tuple[str, ...]
    grants: tuple[str, ...]
    max_sessions: int

    def to_json(self) -> dict:
        return {k: list(v) if isinstance(v, tuple) else v for k, v in asdict(self).items()}

    @staticmethod
    def from_json(raw: object) -> "Snapshot":
        names = {"owns", "routes", "forbidden", "needs_user", "grants", "max_sessions"}
        if not isinstance(raw, dict) or set(raw) != names:
            raise ValueError("manifest snapshot keys are wrong")
        lists = {k: tuple(str(x) for x in raw[k]) for k in names - {"max_sessions"}}
        if not isinstance(raw["max_sessions"], int):
            raise ValueError("max_sessions must be an int")
        return Snapshot(max_sessions=raw["max_sessions"], **lists)


@dataclass(frozen=True)
class Change:
    lines: tuple[str, ...]
    authority_reduced: bool


def manifest_digest(root: Path = REPO_ROOT) -> str:
    h = hashlib.sha256()
    for rel in (ROLES_REL_PATH, AUTHORITY_REL_PATH):
        h.update((root / rel).read_bytes())
    return h.hexdigest()[:16]


def snapshot(role_id: str, roster: Roster, authority: Authority) -> Snapshot:
    role = roster.role(role_id)
    if role is None:
        raise KeyError(role_id)
    base = authority.for_function(role.function)
    return Snapshot(
        owns=tuple(role.owns),
        routes=tuple(f"{g} -> {t}" for g, t in role.routes),
        forbidden=tuple(base.forbidden) if base else (),
        needs_user=tuple(base.needs_user) if base else (),
        grants=tuple(f"{'/'.join(g.actions)}@{g.scope}" for g in authority.grants_for(role_id)),
        max_sessions=role.max_sessions,
    )


def _delta(label: str, old: tuple[str, ...], new: tuple[str, ...]) -> str | None:
    added, removed = sorted(set(new) - set(old)), sorted(set(old) - set(new))
    if not added and not removed:
        return None
    parts = ([f"+{', '.join(added)}"] if added else []) + ([f"-{', '.join(removed)}"] if removed else [])
    return f"{label}: {'; '.join(parts)}"


def diff(old: Snapshot, new: Snapshot) -> Change:
    lines = [d for d in (
        _delta("owns", old.owns, new.owns), _delta("routes", old.routes, new.routes),
        _delta("forbidden", old.forbidden, new.forbidden), _delta("needs the user", old.needs_user, new.needs_user),
        _delta("grants", old.grants, new.grants),
    ) if d]
    if old.max_sessions != new.max_sessions:
        lines.append(f"max_sessions: {old.max_sessions} -> {new.max_sessions}")
    reduced = bool(set(new.forbidden) - set(old.forbidden) or set(new.needs_user) - set(old.needs_user)
                   or set(old.grants) - set(new.grants))
    return Change(tuple(lines), reduced)
