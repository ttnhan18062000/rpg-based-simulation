#!/usr/bin/env python3
"""Read-only freshness check: `python3 tools/sessions/settings_freshness.py [dir] [--ref origin/main]`.

TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS. A session started from a directory outside the repo, or from a
checkout whose `.claude/settings.json` and `.claude/agents/` are behind origin/main, runs without the project hooks (the
session guard, the manual-action sampler, role stamping) and without the project agent types. Nothing says so at start,
so the instruments stay dark. This reports it, by CONTENT against the ref (not by commit distance).

Exit 0 = match, 1 = mismatch (outside the repo, a differing file, a missing hook), 2 = cannot verify (the ref is
missing, e.g. no fetch yet). Never fetches, never writes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

OK, MISMATCH, UNKNOWN = "ok", "mismatch", "unknown"
SETTINGS, AGENTS = ".claude/settings.json", ".claude/agents"
EXIT = {OK: 0, MISMATCH: 1, UNKNOWN: 2}


@dataclass
class Report:
    directory: str
    status: str = OK
    inside_repo: bool = True
    problems: list[str] = field(default_factory=list)
    missing_hooks: list[str] = field(default_factory=list)

    def fail(self, message: str, status: str = MISMATCH) -> None:
        self.problems.append(message)
        if self.status != MISMATCH:
            self.status = status

    def lines(self) -> list[str]:
        head = {OK: "settings and agents match", MISMATCH: "STALE OR OUTSIDE THE REPO", UNKNOWN: "cannot verify"}[self.status]
        return [f"{self.directory}: {head}"] + [f"  - {p}" for p in self.problems] + \
            [f"  - missing hook: {h}" for h in self.missing_hooks]


def _git(args: list[str], cwd: Path, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=not binary, timeout=30)


def _hook_commands(settings: dict) -> set[str]:
    """`<event>: <command>` for every hook command in a settings document."""
    out: set[str] = set()
    for event, groups in (settings.get("hooks") or {}).items():
        for group in groups or []:
            for hook in group.get("hooks") or []:
                if hook.get("command"):
                    out.add(f"{event}: {hook['command']}")
    return out


def _json(text: str | bytes | None) -> dict:
    try:
        data = json.loads(text or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _ref_files(top: Path, ref: str) -> dict[str, bytes] | None:
    listing = _git(["ls-tree", "-r", "--name-only", ref, "--", AGENTS], top)
    if listing.returncode != 0:
        return None
    files = {}
    for name in listing.stdout.splitlines():
        blob = _git(["show", f"{ref}:{name}"], top, binary=True)
        if blob.returncode == 0:
            files[name] = blob.stdout
    return files


def check(directory: Path | str, ref: str = "origin/main") -> Report:
    directory = Path(directory)
    report = Report(str(directory))
    if not directory.is_dir():
        report.inside_repo = False
        report.fail("the directory does not exist")
        return report
    top = _git(["rev-parse", "--show-toplevel"], directory)
    if top.returncode != 0:
        report.inside_repo = False
        report.fail("not inside a git repository: the project .claude/settings.json, agent types and workflows are not "
                    "loaded from here (\"agent type '...' not found\", session_role stays unresolved)")
        return report
    root = Path(top.stdout.strip())
    ref_settings = _git(["show", f"{ref}:{SETTINGS}"], root)
    ref_files = _ref_files(root, ref)
    if ref_settings.returncode != 0 or ref_files is None:
        report.fail(f"cannot read {ref}:{SETTINGS} (no such ref; run `git fetch origin` first)", UNKNOWN)
        return report
    local_path = root / SETTINGS
    local = local_path.read_text(encoding="utf-8") if local_path.is_file() else None
    if local is None:
        report.fail(f"{SETTINGS} is missing")
    elif _json(local) != _json(ref_settings.stdout):
        report.fail(f"{SETTINGS} differs from {ref}")
    report.missing_hooks = sorted(_hook_commands(_json(ref_settings.stdout)) - _hook_commands(_json(local)))
    if report.missing_hooks:
        report.fail(f"{len(report.missing_hooks)} hook command(s) on {ref} are not in the local settings")
    for name, content in sorted(ref_files.items()):
        path = root / name
        if not path.is_file():
            report.fail(f"{name} is missing locally")
        elif path.read_bytes() != content:
            report.fail(f"{name} differs from {ref}")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Report whether a directory runs the project settings and agents on the ref.")
    ap.add_argument("directory", nargs="?", default=".")
    ap.add_argument("--ref", default="origin/main")
    a = ap.parse_args(argv)
    report = check(a.directory, a.ref)
    print("\n".join(report.lines()))
    return EXIT[report.status]


if __name__ == "__main__":
    sys.exit(main())
