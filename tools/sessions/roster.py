"""Typed, read-only loader for the session role manifest and the authority file.

Source of truth: `registries/session_roles.yaml` and `registries/session_authority.yaml`
(plan `docs/plans/agent_infrastructure/session_layer_working_process.md`, sections 3, 4 and 10).
This module only reads. Nothing here writes a file or stores liveness: who is running a seat is
runtime state and derivable (M0 item q), so no field of these records holds it.

Callers get frozen dataclasses; the raw YAML mapping does not leave this module.
A malformed file raises `RosterError` with the path and the reason, never a bare KeyError.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ROLES_REL_PATH = Path("registries/session_roles.yaml")
AUTHORITY_REL_PATH = Path("registries/session_authority.yaml")

FUNCTIONS = ("designer", "planner", "implementer")
SEAT_STATUSES = ("staffed", "unstaffed")


class RosterError(ValueError):
    """The manifest or authority file is not shaped as the loader requires."""


@dataclass(frozen=True)
class Domain:
    name: str
    owns: tuple[str, ...]
    owns_not: tuple[str, ...]
    routes: tuple[tuple[str, str], ...]  # (glob, target role id), in file order


@dataclass(frozen=True)
class OwnershipSplit:
    paths: tuple[str, ...]
    domains: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class Role:
    role: str
    domain: str
    function: str
    session_name: str
    legacy_session_name: str | None
    seat_status: str
    interim_holder: str | None
    owns: tuple[str, ...]
    owns_not: tuple[str, ...]
    routes: tuple[tuple[str, str], ...]
    accepts_dispatch_from: tuple[str, ...]
    may_write: tuple[str, ...]
    tools: tuple[str, ...] | None  # None = inherit the session's tools; a tuple is an allowlist
    worktree: str
    max_sessions: int
    handover: str
    overrides: tuple[str, ...]  # which of owns / owns_not / routes this entry overrides


@dataclass(frozen=True)
class Worktree:
    name: str
    writer: str | None


@dataclass(frozen=True)
class Grant:
    actions: tuple[str, ...]
    scope: str
    date: str
    quote: str
    source: str


@dataclass(frozen=True)
class FunctionAuthority:
    forbidden: tuple[str, ...]
    needs_user: tuple[str, ...]


@dataclass(frozen=True)
class Roster:
    domains: tuple[Domain, ...]
    splits: tuple[OwnershipSplit, ...]
    roles: tuple[Role, ...]
    worktrees: tuple[Worktree, ...]

    def role(self, role_id: str) -> Role | None:
        return next((r for r in self.roles if r.role == role_id), None)

    @property
    def role_ids(self) -> tuple[str, ...]:
        return tuple(r.role for r in self.roles)


@dataclass(frozen=True)
class Authority:
    governing_file: bool
    function_defaults: tuple[tuple[str, FunctionAuthority], ...]
    grants: tuple[tuple[str, tuple[Grant, ...]], ...]  # (role id, grants)

    def for_function(self, function: str) -> FunctionAuthority | None:
        return dict(self.function_defaults).get(function)

    def grants_for(self, role_id: str) -> tuple[Grant, ...]:
        return dict(self.grants).get(role_id, ())


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RosterError(f"{path}: cannot read: {exc}") from exc
    except yaml.YAMLError as exc:
        raise RosterError(f"{path}: not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise RosterError(f"{path}: top level must be a mapping")
    return data


def _strs(value: Any, where: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise RosterError(f"{where}: must be a list of strings")
    return tuple(value)


def _routes(value: Any, where: str) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        raise RosterError(f"{where}: must map a glob to a role id")
    return tuple(value.items())


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise RosterError(f"{where}: must be a mapping")
    return value


def _require(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise RosterError(f"{where}: missing required field {key!r}")
    return mapping[key]


def _parse_role(entry: Any, domains: dict[str, Domain]) -> Role:
    if not isinstance(entry, dict):
        raise RosterError("roles: each entry must be a mapping")
    role_id = _require(entry, "role", "roles[]")
    where = f"role {role_id}"
    identity = _mapping(_require(entry, "identity", where), f"{where}.identity")
    responsibility = _mapping(entry.get("responsibility"), f"{where}.responsibility")
    capability = _mapping(entry.get("capability"), f"{where}.capability")
    placement = _mapping(_require(entry, "placement", where), f"{where}.placement")
    domain_name = _require(identity, "domain", f"{where}.identity")
    if domain_name not in domains:
        raise RosterError(f"{where}: unknown domain {domain_name!r}")
    domain = domains[domain_name]
    overrides = tuple(k for k in ("owns", "owns_not", "routes") if k in responsibility)
    tools = capability.get("tools")
    return Role(
        role=role_id,
        domain=domain_name,
        function=_require(identity, "function", f"{where}.identity"),
        session_name=_require(identity, "session_name", f"{where}.identity"),
        legacy_session_name=identity.get("legacy_session_name"),
        seat_status=_require(identity, "seat_status", f"{where}.identity"),
        interim_holder=identity.get("interim_holder"),
        owns=_strs(responsibility["owns"], f"{where}.owns") if "owns" in responsibility else domain.owns,
        owns_not=(
            _strs(responsibility["owns_not"], f"{where}.owns_not") if "owns_not" in responsibility else domain.owns_not
        ),
        routes=_routes(responsibility["routes"], f"{where}.routes") if "routes" in responsibility else domain.routes,
        accepts_dispatch_from=_strs(responsibility.get("accepts_dispatch_from"), f"{where}.accepts_dispatch_from"),
        may_write=_strs(capability.get("may_write"), f"{where}.may_write"),
        tools=None if tools is None else _strs(tools, f"{where}.tools"),
        worktree=_require(placement, "worktree", f"{where}.placement"),
        max_sessions=int(placement.get("max_sessions", 1)),
        handover=_require(entry, "handover", where),
        overrides=overrides,
    )


def load_roster(root: Path = REPO_ROOT) -> Roster:
    path = root / ROLES_REL_PATH
    data = _read_yaml(path)
    domains: dict[str, Domain] = {}
    for name, body in _mapping(data.get("domains"), "domains").items():
        body = _mapping(body, f"domain {name}")
        domains[name] = Domain(
            name=name,
            owns=_strs(body.get("owns"), f"domain {name}.owns"),
            owns_not=_strs(body.get("owns_not"), f"domain {name}.owns_not"),
            routes=_routes(body.get("routes"), f"domain {name}.routes"),
        )
    splits = tuple(
        OwnershipSplit(
            paths=_strs(_require(s, "paths", "ownership_splits[]"), "ownership_splits[].paths"),
            domains=_strs(_require(s, "domains", "ownership_splits[]"), "ownership_splits[].domains"),
            reason=str(_require(s, "reason", "ownership_splits[]")),
        )
        for s in (data.get("ownership_splits") or [])
    )
    roles = tuple(_parse_role(e, domains) for e in (data.get("roles") or []))
    worktrees = tuple(
        Worktree(name=n, writer=_mapping(b, f"worktree {n}").get("writer"))
        for n, b in _mapping(data.get("worktrees"), "worktrees").items()
    )
    return Roster(domains=tuple(domains.values()), splits=splits, roles=roles, worktrees=worktrees)


def load_authority(root: Path = REPO_ROOT) -> Authority:
    path = root / AUTHORITY_REL_PATH
    data = _read_yaml(path)
    defaults = tuple(
        (
            function,
            FunctionAuthority(
                forbidden=_strs(_mapping(body, f"function_defaults.{function}").get("forbidden"), "forbidden"),
                needs_user=_strs(_mapping(body, f"function_defaults.{function}").get("needs_user"), "needs_user"),
            ),
        )
        for function, body in _mapping(data.get("function_defaults"), "function_defaults").items()
    )
    grants = tuple(
        (
            role_id,
            tuple(
                Grant(
                    actions=_strs(_require(g, "action", f"authority.{role_id}.grants[]"), "action"),
                    scope=str(_require(g, "scope", f"authority.{role_id}.grants[]")),
                    date=str(_require(g, "date", f"authority.{role_id}.grants[]")),
                    quote=str(_require(g, "quote", f"authority.{role_id}.grants[]")),
                    source=str(_require(g, "source", f"authority.{role_id}.grants[]")),
                )
                for g in (_mapping(body, f"authority.{role_id}").get("grants") or [])
            ),
        )
        for role_id, body in _mapping(data.get("authority"), "authority").items()
    )
    return Authority(
        governing_file=bool(data.get("governing_file", False)),
        function_defaults=defaults,
        grants=grants,
    )
