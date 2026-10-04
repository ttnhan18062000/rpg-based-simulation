"""Runtime role state: `<git-common-dir>/session-roles/<role-id>/` and the worktree writer lease.

Plan `docs/plans/agent_infrastructure/session_layer_working_process.md`, sections 5 and 6.1. The role id
is the permanent identity; a session is a disposable instance, so everything needed to find or replace an
instance after a crash is recoverable from the role id alone.

Layout (per user and per machine, never committed; the git common directory is the same from every
worktree and survives the removal of any one of them):

    <common-dir>/session-roles/<role-id>/bindings.jsonl   append-only, one `Binding` per SessionStart
    <common-dir>/session-roles/<role-id>/instance.json    the current holder and whether it was released
    <common-dir>/session-roles/_leases/<digest>.json      the writer lease, keyed by PHYSICAL worktree path

Liveness is never stored. `instance.json` records the holder and `released`; `live` versus `orphaned` is
computed on read from `/proc`: a recorded pid is live only if `/proc/<pid>` exists and its start time and
command line equal what was recorded (pids are reused). The inbox socket file is never read: after `kill -9`
it stays behind, so it says nothing about the process (M0q/r).

Lease mechanism (decided here, from M0 evidence): a file, not a git-native construct. It is keyed by the
physical worktree path (a domain may have several physical worktrees, each with its own writer), lives
beside the role state so one directory holds all runtime state, and is created atomically (`O_EXCL`) or
replaced under a lock. A stale lease is reported, never stolen: only the same role re-taking it, or an
explicit `release_lease` by the user, clears it.

Callers get frozen dataclasses; no raw dict leaves this module. A malformed file raises `StateError`.
Nothing here writes outside the role-state directory.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

STATE_DIRNAME = "session-roles"
LEASE_DIRNAME = "_leases"
BINDINGS = "bindings.jsonl"
INSTANCE = "instance.json"

LIVE, ORPHANED, RELEASED = "live", "orphaned", "released"
_ROLE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class StateError(ValueError):
    """A state file is malformed, or a role id / path is unusable."""


class LeaseRefused(StateError):
    """The worktree's writer lease is held by another role (live or stale); never taken silently."""

    def __init__(self, message: str, lease: "Lease", liveness: str, age_seconds: float):
        super().__init__(message)
        self.lease, self.liveness, self.age_seconds = lease, liveness, age_seconds


@dataclass(frozen=True)
class ProcessId:
    """A process as recorded: pid plus the start time and command line that make it recognisable."""

    pid: int
    start: str  # field 22 of /proc/<pid>/stat (clock ticks since boot), as text
    cmdline: str


@dataclass(frozen=True)
class Binding:
    session_id: str
    role: str
    source: str
    worktree: str
    branch: str
    transcript_path: str  # a hint only: recovery looks a transcript up by session id
    process: ProcessId | None
    manifest_digest: str
    ts: str


@dataclass(frozen=True)
class Instance:
    role: str
    holder: Binding
    released: bool
    released_at: str | None


@dataclass(frozen=True)
class Lease:
    worktree: str  # physical, resolved path
    role: str
    session_id: str
    process: ProcessId | None
    ts: str


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _check_role(role: str) -> str:
    if not _ROLE_ID.match(role or ""):
        raise StateError(f"unusable role id {role!r} (lowercase letters, digits and '-' only)")
    return role


# ---- locations ---------------------------------------------------------------------------------

def common_dir(cwd: Path | str = ".") -> Path:
    """The git common directory: the same absolute path from every worktree of this repository."""
    out = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=str(cwd), capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise StateError(f"not in a git repository: {out.stderr.strip()}")
    return Path(out.stdout.strip())


def state_root(cwd: Path | str = ".") -> Path:
    return common_dir(cwd) / STATE_DIRNAME


def role_dir(root: Path, role: str) -> Path:
    return root / _check_role(role)


def lease_path(root: Path, worktree: Path | str) -> Path:
    digest = hashlib.sha256(str(Path(worktree).resolve()).encode()).hexdigest()[:20]
    return root / LEASE_DIRNAME / f"{digest}.json"


# ---- liveness ----------------------------------------------------------------------------------

def process_identity(pid: int, proc_root: Path = Path("/proc")) -> ProcessId | None:
    """The pid's recognisable identity, or None when `/proc/<pid>` does not exist."""
    try:
        stat = (proc_root / str(pid) / "stat").read_text()
        raw = (proc_root / str(pid) / "cmdline").read_bytes()
    except OSError:
        return None
    # field 2 (comm) is parenthesised and may contain spaces; the fields after it are space separated
    after = stat[stat.rindex(")") + 2:].split()
    start = after[19]  # field 22 overall
    return ProcessId(pid=pid, start=start, cmdline=raw.replace(b"\0", b" ").decode(errors="replace").strip())


def is_live(process: ProcessId | None, proc_root: Path = Path("/proc")) -> bool:
    """Live only if the recorded pid exists AND its start time and command line match what was recorded."""
    if process is None:
        return False
    current = process_identity(process.pid, proc_root)
    return current is not None and current.start == process.start and current.cmdline == process.cmdline


def liveness(instance: Instance, proc_root: Path = Path("/proc")) -> str:
    """`released`, else `live` / `orphaned` computed from /proc. Never written to disk."""
    if instance.released:
        return RELEASED
    return LIVE if is_live(instance.holder.process, proc_root) else ORPHANED


# ---- (de)serialisation -------------------------------------------------------------------------

def _process_from(raw: Any, where: str) -> ProcessId | None:
    if raw is None:
        return None
    if not isinstance(raw, dict) or set(raw) != {"pid", "start", "cmdline"}:
        raise StateError(f"{where}: process must be null or {{pid, start, cmdline}}")
    if not isinstance(raw["pid"], int) or not isinstance(raw["start"], str) or not isinstance(raw["cmdline"], str):
        raise StateError(f"{where}: process fields have the wrong types")
    return ProcessId(raw["pid"], raw["start"], raw["cmdline"])


def _binding_from(raw: Any, where: str) -> Binding:
    names = {f.name for f in fields(Binding)}
    if not isinstance(raw, dict) or set(raw) != names:
        raise StateError(f"{where}: binding keys must be exactly {sorted(names)}")
    for key in names - {"process"}:
        if not isinstance(raw[key], str):
            raise StateError(f"{where}: binding.{key} must be a string")
    return Binding(process=_process_from(raw["process"], where), **{k: raw[k] for k in names - {"process"}})


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StateError(f"{path}: unreadable ({exc})") from exc


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


@contextmanager
def _locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def write_role_file(root: Path, role: str, name: str, payload: dict) -> None:
    """Atomic write of one JSON file inside the role's own state directory (nothing outside it)."""
    if "/" in name or name.startswith("."):
        raise StateError(f"unusable role file name {name!r}")
    _atomic_write(role_dir(root, role) / name, payload)


def read_role_file(root: Path, role: str, name: str) -> Any | None:
    path = role_dir(root, role) / name
    return _read_json(path) if path.is_file() else None


# ---- bindings and instance ---------------------------------------------------------------------

def append_binding(root: Path, binding: Binding) -> None:
    """Atomic append: one O_APPEND write of one line under a lock, so parallel writers never interleave."""
    path = role_dir(root, binding.role) / BINDINGS
    line = json.dumps(asdict(binding), sort_keys=True) + "\n"
    with _locked(path.with_suffix(".lock")):
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)


def read_bindings(root: Path, role: str) -> list[Binding]:
    path = role_dir(root, role) / BINDINGS
    if not path.is_file():
        return []
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                out.append(_binding_from(json.loads(line), f"{path}:{n}"))
            except ValueError as exc:
                if isinstance(exc, StateError):
                    raise
                raise StateError(f"{path}:{n}: not valid JSON ({exc})") from exc
    return out


def record_start(root: Path, binding: Binding) -> Instance:
    """A SessionStart: append the binding and make it the instance's holder (clears a prior `released`)."""
    append_binding(root, binding)
    instance = Instance(role=binding.role, holder=binding, released=False, released_at=None)
    _write_instance(root, instance)
    return instance


def _write_instance(root: Path, instance: Instance) -> None:
    _atomic_write(role_dir(root, instance.role) / INSTANCE, {
        "role": instance.role, "holder": asdict(instance.holder),
        "released": instance.released, "released_at": instance.released_at,
    })


def read_instance(root: Path, role: str) -> Instance | None:
    path = role_dir(root, role) / INSTANCE
    if not path.is_file():
        return None
    raw = _read_json(path)
    if not isinstance(raw, dict) or set(raw) != {"role", "holder", "released", "released_at"}:
        raise StateError(f"{path}: instance keys must be role, holder, released, released_at")
    if not isinstance(raw["released"], bool) or raw["role"] != role:
        raise StateError(f"{path}: released must be a boolean and role must match the directory")
    return Instance(role=role, holder=_binding_from(raw["holder"], str(path)),
                    released=raw["released"], released_at=raw["released_at"])


def release(root: Path, role: str) -> Instance:
    """Explicit clean end or retirement: the only thing that ever sets `released`."""
    instance = read_instance(root, role)
    if instance is None:
        raise StateError(f"role {role!r} has no instance to release")
    done = Instance(role=role, holder=instance.holder, released=True, released_at=_now())
    _write_instance(root, done)
    return done


# ---- writer lease ------------------------------------------------------------------------------

def _lease_to_json(lease: Lease) -> dict:
    return asdict(lease)


def read_lease(root: Path, worktree: Path | str) -> Lease | None:
    path = lease_path(root, worktree)
    if not path.is_file():
        return None
    raw = _read_json(path)
    names = {f.name for f in fields(Lease)}
    if not isinstance(raw, dict) or set(raw) != names:
        raise StateError(f"{path}: lease keys must be exactly {sorted(names)}")
    for key in ("worktree", "role", "session_id", "ts"):
        if not isinstance(raw[key], str):
            raise StateError(f"{path}: lease.{key} must be a string")
    return Lease(raw["worktree"], raw["role"], raw["session_id"], _process_from(raw["process"], str(path)), raw["ts"])


def take_lease(root: Path, worktree: Path | str, role: str, session_id: str,
               process: ProcessId | None, proc_root: Path = Path("/proc")) -> Lease:
    """Take the worktree's writer lease for `role`.

    No lease: created. The same role re-taking (after `/clear`, a resume or a replace): succeeds and replaces
    the holder. Another role: refused with `LeaseRefused` carrying the holder, whether it is live or stale, and
    its age. A stale lease is reported, never taken.
    """
    _check_role(role)
    physical = str(Path(worktree).resolve())
    path = lease_path(root, physical)
    new = Lease(worktree=physical, role=role, session_id=session_id, process=process, ts=_now())
    with _locked(path.with_suffix(".lock")):
        held = read_lease(root, physical)
        if held is not None and held.role != role:
            state = LIVE if is_live(held.process, proc_root) else "stale"
            age = (datetime.now(timezone.utc) - _parse_ts(held.ts)).total_seconds()
            raise LeaseRefused(
                f"writer lease for {physical} is held by {held.role!r} ({state}, {int(age)}s old, session "
                f"{held.session_id}); release it explicitly if that holder is gone",
                held, state, age,
            )
        _atomic_write(path, _lease_to_json(new))
    return new


def release_lease(root: Path, worktree: Path | str) -> bool:
    """Explicit, by the user. Returns whether a lease existed."""
    path = lease_path(root, worktree)
    with _locked(path.with_suffix(".lock")):
        if not path.is_file():
            return False
        path.unlink()
        return True


# ---- CLI ---------------------------------------------------------------------------------------

def _describe(root: Path, role: str) -> str:
    instance = read_instance(root, role)
    if instance is None:
        return f"{role}: no instance recorded"
    h = instance.holder
    state = liveness(instance)
    pid = h.process.pid if h.process else "unknown"
    lines = [f"{role}: {state}", f"  holder session {h.session_id} (pid {pid}, source {h.source}, {h.ts})",
             f"  worktree {h.worktree} on {h.branch or '?'}"]
    if instance.released:
        lines.append(f"  released at {instance.released_at}")
    lease = read_lease(root, h.worktree) if h.worktree else None
    if lease is not None:
        age = int((datetime.now(timezone.utc) - _parse_ts(lease.ts)).total_seconds())
        lines.append(f"  writer lease on that worktree: {lease.role} ({'live' if is_live(lease.process) else 'stale'}, {age}s old)")
    lines.append(f"  bindings recorded: {len(read_bindings(root, role))}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Show or release a role's runtime state.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show").add_argument("role")
    sub.add_parser("release").add_argument("role")
    a = ap.parse_args(argv)
    try:
        root = state_root()
        if a.cmd == "show":
            print(_describe(root, a.role))
        else:
            release(root, a.role)
            print(f"released {a.role}")
    except StateError as exc:
        print(f"state: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
