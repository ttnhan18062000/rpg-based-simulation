#!/usr/bin/env python3
"""Answer "who owns this path?" from the session role manifest (plan section 9.1).

Read-only and path-only: no free-text topic lookup, no liveness. The result names a *seat* (a role id);
whether that seat is running is a model-side `ListAgents` call, never computed here.

Resolution:
  1. A path matched by an `ownership_splits` entry returns every domain the split names, with its reason.
  2. Otherwise each domain's `owns` globs are matched (a glob also listed in that domain's `owns_not`
     excludes the domain); the longest matching glob wins across domains.
  3. Nothing owns the path: `unowned`, never a guess.
The contact seat is the owning domain's planner (dispatch goes through the planner, plan 9.0). With
`--from <domain>`, a path that domain does not own is first looked up in that domain's `routes`.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from tools.sessions.roster import REPO_ROOT, Domain, Roster, RosterError, load_roster

OWNED = "owned"
SPLIT = "split"
UNOWNED = "unowned"


@dataclass(frozen=True)
class RouteResult:
    path: str
    status: str  # OWNED | SPLIT | UNOWNED
    domains: tuple[str, ...]
    seats: tuple[str, ...]  # role ids to contact; never a session, never a liveness claim
    matched_glob: str | None
    reason: str


@lru_cache(maxsize=None)
def _glob_regex(pattern: str) -> re.Pattern[str]:
    """`**` crosses directories, `*` and `?` stay inside one path segment."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("".join(out) + r"\Z")


def _matches(pattern: str, path: str) -> bool:
    return _glob_regex(pattern).match(path) is not None


def _normalise(path: str) -> str:
    return path.replace("\\", "/").removeprefix("./")


def _best_glob(patterns: tuple[str, ...], path: str) -> str | None:
    hits = [p for p in patterns if _matches(p, path)]
    return max(hits, key=len) if hits else None


def _planner_seat(roster: Roster, domain: str) -> str | None:
    planner = next((r for r in roster.roles if r.domain == domain and r.function == "planner"), None)
    return planner.role if planner else None


def _domain_claim(domain: Domain, path: str) -> str | None:
    """The domain's longest `owns` glob matching the path, unless an `owns_not` glob excludes it."""
    if _best_glob(domain.owns_not, path):
        return None
    return _best_glob(domain.owns, path)


def route(path: str, roster: Roster | None = None, from_domain: str | None = None) -> RouteResult:
    roster = roster or load_roster()
    path = _normalise(path)
    known = {d.name: d for d in roster.domains}
    if from_domain is not None and from_domain not in known:
        raise RosterError(f"unknown domain {from_domain!r}; known: {', '.join(sorted(known))}")

    for split in roster.splits:
        glob_ = _best_glob(split.paths, path)
        if glob_:
            seats = tuple(s for s in (_planner_seat(roster, d) for d in split.domains) if s)
            return RouteResult(path, SPLIT, split.domains, seats, glob_, split.reason)

    claims = {d.name: g for d in roster.domains if (g := _domain_claim(d, path))}
    if from_domain is not None and from_domain not in claims:
        target = next((t for g, t in known[from_domain].routes if _matches(g, path)), None)
        if target is not None:
            role = roster.role(target)
            domain = (role.domain,) if role else ()
            return RouteResult(path, OWNED, domain, (target,), None, f"{from_domain} routes this path to {target}")

    if not claims:
        return RouteResult(path, UNOWNED, (), (), None, "no domain's owns glob matches this path")
    winner = max(claims, key=lambda name: len(claims[name]))
    seat = _planner_seat(roster, winner)
    return RouteResult(path, OWNED, (winner,), (seat,) if seat else (), claims[winner], f"longest owns glob: {claims[winner]}")


def format_result(result: RouteResult) -> str:
    lines = [f"path: {result.path}", f"status: {result.status}"]
    if result.domains:
        lines.append(f"domain: {', '.join(result.domains)}")
    if result.seats:
        lines.append(f"seat: {', '.join(result.seats)}")
    if result.matched_glob:
        lines.append(f"matched: {result.matched_glob}")
    lines.append(f"reason: {result.reason}")
    lines.append("liveness: not computed here; check with ListAgents")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Who owns this path? (reads the session role manifest only)")
    parser.add_argument("path", help="repo-relative path")
    parser.add_argument("--from", dest="from_domain", default=None, help="asking domain: applies its `routes` first")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        result = route(args.path, load_roster(args.root), args.from_domain)
    except RosterError as exc:
        print(f"route: {exc}", file=sys.stderr)
        return 2
    print(format_result(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
