#!/usr/bin/env python3
"""Validate the session role manifest and authority file (plan section 4, "Rules the validator enforces").

Read-only. `validate(root)` returns `Finding`s for rule violations (exit code 1 from the CLI) and
`complexity_report(roster)` returns report-only numbers (never changes the exit code).

Rules (each has a named `rule` id on its finding):
  glob-matches-nothing     an `owns` glob resolves to no file
  overlapping-ownership    two domains own the same file and no `ownership_splits` entry covers it
  missing-handover         a role has no handover path, or the path is not `.claude/handover/<role>.md`
  unknown-route-target     a `routes` target (or `accepts_dispatch_from` / `interim_holder`) is not a role
  duplicate-session-name   two roles share a `session_name`
  worktree-writer          a worktree declares no writer, or a role names a worktree that is not declared
  writer-not-implementer   a worktree's writer is not an implementer
  bad-field                function / seat_status / max_sessions is outside its allowed values
  authority-*              the authority file is not marked governing, names an unknown role, or lacks a
                           default for a function
  stale-citation           the manifest cites a ticket id that no ticket file carries
  generated-drift          a committed `.claude/agents/session-*.md` differs from a fresh generation

Unstaffed seats are valid only with a named `interim_holder` that is a real role (plan section 3).
"""

from __future__ import annotations

import argparse
import glob as _glob
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from tools.sessions.card import TEMPLATE_DIR
from tools.sessions.generate_agents import check_generated
from tools.sessions.roster import (
    AUTHORITY_REL_PATH,
    FUNCTIONS,
    REPO_ROOT,
    ROLES_REL_PATH,
    SEAT_STATUSES,
    Authority,
    Roster,
    RosterError,
    load_authority,
    load_roster,
)

_TICKET_ID = re.compile(r"TCK-\d{8}-[A-Z0-9][A-Z0-9-]*")
_GLOB_CHARS = set("*?[")


@dataclass(frozen=True)
class Finding:
    rule: str
    subject: str
    message: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.subject}: {self.message}"


def _is_glob(pattern: str) -> bool:
    return any(c in pattern for c in _GLOB_CHARS)


def _files(root: Path, pattern: str) -> set[str]:
    """Files under `root` matched by `pattern` (`**` recursive), as repo-relative posix paths."""
    hits = _glob.glob(str(root / pattern), recursive=True)
    return {Path(h).relative_to(root).as_posix() for h in hits if Path(h).is_file()}


def _covered_by_split(roster: Roster, rel: str, a: str, b: str, root: Path) -> bool:
    for split in roster.splits:
        if a in split.domains and b in split.domains:
            if any(rel in _files(root, p) for p in split.paths):
                return True
    return False


def _check_fields(roster: Roster) -> list[Finding]:
    out: list[Finding] = []
    for r in roster.roles:
        if r.function not in FUNCTIONS:
            out.append(Finding("bad-field", r.role, f"function {r.function!r} not in {list(FUNCTIONS)}"))
        if r.seat_status not in SEAT_STATUSES:
            out.append(Finding("bad-field", r.role, f"seat_status {r.seat_status!r} not in {list(SEAT_STATUSES)}"))
        if r.max_sessions < 1:
            out.append(Finding("bad-field", r.role, "max_sessions must be >= 1"))
        if r.session_name != r.role:
            out.append(Finding("bad-field", r.role, f"session_name {r.session_name!r} must equal the role id"))
        if r.seat_status == "unstaffed" and not r.interim_holder:
            out.append(Finding("bad-field", r.role, "an unstaffed seat must name its interim_holder"))
    return out


def _check_names(roster: Roster) -> list[Finding]:
    out: list[Finding] = []
    seen: dict[str, str] = {}
    for r in roster.roles:
        if r.session_name in seen:
            out.append(Finding("duplicate-session-name", r.role, f"{r.session_name!r} already used by {seen[r.session_name]}"))
        seen[r.session_name] = r.role
    ids = [r.role for r in roster.roles]
    for dup in {i for i in ids if ids.count(i) > 1}:
        out.append(Finding("duplicate-session-name", dup, "role id appears more than once"))
    return out


def _check_references(roster: Roster) -> list[Finding]:
    out: list[Finding] = []
    known = set(roster.role_ids)
    for r in roster.roles:
        for glob_, target in r.routes:
            if target not in known:
                out.append(Finding("unknown-route-target", r.role, f"route {glob_!r} -> {target!r} is not a role"))
        for source in r.accepts_dispatch_from:
            if source != "user" and source not in known:
                out.append(Finding("unknown-route-target", r.role, f"accepts_dispatch_from {source!r} is not a role"))
        if r.interim_holder and r.interim_holder not in known:
            out.append(Finding("unknown-route-target", r.role, f"interim_holder {r.interim_holder!r} is not a role"))
    for d in roster.domains:
        for glob_, target in d.routes:
            if target not in known:
                out.append(Finding("unknown-route-target", f"domain {d.name}", f"route {glob_!r} -> {target!r} is not a role"))
    return out


def _check_handover(roster: Roster) -> list[Finding]:
    out: list[Finding] = []
    for r in roster.roles:
        expected = f".claude/handover/{r.role}.md"
        if not r.handover:
            out.append(Finding("missing-handover", r.role, "no handover path"))
        elif r.handover != expected:
            out.append(Finding("missing-handover", r.role, f"handover {r.handover!r} must be {expected!r}"))
    return out


def _check_worktrees(roster: Roster) -> list[Finding]:
    out: list[Finding] = []
    declared = {w.name: w for w in roster.worktrees}
    for r in roster.roles:
        if r.worktree not in declared:
            out.append(Finding("worktree-writer", r.role, f"worktree {r.worktree!r} is not declared under worktrees:"))
    for w in roster.worktrees:
        if not w.writer:
            out.append(Finding("worktree-writer", w.name, "declares no writer"))
            continue
        writer = roster.role(w.writer)
        if writer is None:
            out.append(Finding("worktree-writer", w.name, f"writer {w.writer!r} is not a role"))
        elif writer.function != "implementer":
            out.append(Finding("writer-not-implementer", w.name, f"writer {w.writer!r} is a {writer.function}, not an implementer"))
        elif writer.worktree != w.name:
            out.append(Finding("worktree-writer", w.name, f"writer {w.writer!r} is placed in {writer.worktree!r}"))
    return out


def _check_ownership(roster: Roster, root: Path) -> list[Finding]:
    out: list[Finding] = []
    domain_files: dict[str, dict[str, str]] = {}  # domain -> file -> the glob that matched it
    checked: set[tuple[str, str]] = set()
    for r in roster.roles:
        for pattern in r.owns:
            if (r.domain, pattern) in checked and not r.overrides:
                continue
            checked.add((r.domain, pattern))
            hits = _files(root, pattern)
            if not hits:
                out.append(Finding("glob-matches-nothing", r.role, f"owns {pattern!r} resolves to no file"))
            bucket = domain_files.setdefault(r.domain, {})
            for h in hits:
                bucket.setdefault(h, pattern)
    names = sorted(domain_files)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            shared = sorted(set(domain_files[a]) & set(domain_files[b]))
            uncovered = [f for f in shared if not _covered_by_split(roster, f, a, b, root)]
            if uncovered:
                out.append(
                    Finding(
                        "overlapping-ownership",
                        f"{a} / {b}",
                        f"{len(uncovered)} file(s) owned by both with no ownership_splits entry, e.g. {uncovered[0]}",
                    )
                )
    return out


def _check_authority(roster: Roster, authority: Authority) -> list[Finding]:
    out: list[Finding] = []
    if not authority.governing_file:
        out.append(Finding("authority-not-governing", str(AUTHORITY_REL_PATH), "must declare `governing_file: true`"))
    known = set(roster.role_ids)
    for role_id, _grants in authority.grants:
        if role_id not in known:
            out.append(Finding("authority-unknown-role", role_id, "authority entry names a role that is not in the manifest"))
    for function in {r.function for r in roster.roles}:
        if authority.for_function(function) is None:
            out.append(Finding("authority-missing-default", function, "no function_defaults entry"))
    for role_id, grants in authority.grants:
        for g in grants:
            if not (g.quote and g.date):
                out.append(Finding("authority-grant-undated", role_id, "a grant needs a date and a quoted source"))
    return out


def _ticket_ids_on_disk(root: Path) -> set[str]:
    base = root / "agent-working" / "tickets"
    return {p.stem for p in base.rglob("TCK-*.md")} if base.is_dir() else set()


def _check_stale_citations(root: Path) -> list[Finding]:
    cited: dict[str, str] = {}
    for rel in (ROLES_REL_PATH, AUTHORITY_REL_PATH):
        for tid in _TICKET_ID.findall((root / rel).read_text(encoding="utf-8")):
            cited.setdefault(tid, rel.as_posix())
    if not cited:
        return []
    on_disk = _ticket_ids_on_disk(root)
    return [Finding("stale-citation", src, f"cites {tid}, which no ticket file carries") for tid, src in cited.items() if tid not in on_disk]


def _check_generated_files(root: Path) -> list[Finding]:
    """Drift between the committed `.claude/agents/session-*.md` files and a fresh generation.

    Runs only when the root carries the card templates; a bare manifest fixture has nothing to compose."""
    if not (root / TEMPLATE_DIR).is_dir():
        return []
    return [Finding("generated-drift", "session agent files", p) for p in check_generated(root)]


def validate(root: Path = REPO_ROOT) -> list[Finding]:
    roster = load_roster(root)
    authority = load_authority(root)
    return (
        _check_fields(roster)
        + _check_names(roster)
        + _check_references(roster)
        + _check_handover(roster)
        + _check_worktrees(roster)
        + _check_ownership(roster, root)
        + _check_authority(roster, authority)
        + _check_stale_citations(root)
        + _check_generated_files(root)
    )


def complexity_report(roster: Roster) -> dict[str, dict[str, int]]:
    """Per-role numbers, report only. A role that piles up overrides, unique routes and exceptions is
    drifting into a hand-written role instead of composing from its function and domain."""
    route_use: dict[tuple[str, str], int] = {}
    for r in roster.roles:
        for pair in r.routes:
            route_use[pair] = route_use.get(pair, 0) + 1
    return {
        r.role: {
            "overrides": len(r.overrides),
            "unique_routes": sum(1 for pair in r.routes if route_use[pair] == 1),
            "extra_dispatch_sources": len([s for s in r.accepts_dispatch_from if s != "user"]),
        }
        for r in roster.roles
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        findings = validate(args.root)
        roster = load_roster(args.root)
    except RosterError as exc:
        print(f"ERROR: {exc}")
        return 1
    for f in findings:
        print(f)
    print("complexity (report only):")
    for role, numbers in complexity_report(roster).items():
        print(f"  {role}: " + ", ".join(f"{k}={v}" for k, v in numbers.items()))
    print(f"{'FAIL' if findings else 'OK'}: {len(findings)} finding(s), {len(roster.roles)} role(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
