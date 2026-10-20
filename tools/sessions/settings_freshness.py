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

#: The code and registries SessionStart itself runs from the session's own worktree
#: (TCK-20261015-SESSION-CODE-FRESHNESS-AT-SESSION-START). A worktree that lags origin/main here injects the wrong
#: role or handover note without any sign of it.
SESSION_CODE_PATHS = (
    "tools/sessions",
    "tools/handover_home.py",
    "tools/agent-monitoring/session_start_handover_hook.py",
    "registries/session_roles.yaml",
    "registries/session_authority.yaml",
)


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


def stale_session_code(directory: Path | str, ref: str = "origin/main") -> list[str] | None:
    """Session code or registries that changed on `ref` since this checkout diverged from it, so this worktree
    does not have them yet. `[]` when it is current, `None` when that cannot be told (no repo, no ref).

    One `merge-base` and one `diff`, offline, never a fetch. It compares against the merge base, not against the
    ref's content, so a branch that itself edits session code is not reported as stale (the launch-time settings
    check above compares content on purpose; this one runs on every start and must not cry wolf on its authors).
    Files this branch also changed still show: they need the merge too."""
    directory = Path(directory)
    top = _git(["rev-parse", "--show-toplevel"], directory) if directory.is_dir() else None
    if top is None or top.returncode != 0:
        return None
    root = Path(top.stdout.strip())
    base = _git(["merge-base", "HEAD", ref], root)
    if base.returncode != 0 or not base.stdout.strip():
        return None
    diff = _git(["diff", "--name-only", base.stdout.strip(), ref, "--", *SESSION_CODE_PATHS], root)
    if diff.returncode != 0:
        return None
    return sorted(line for line in diff.stdout.splitlines() if line)


def session_code_line(directory: Path | str, ref: str = "origin/main") -> str:
    """The one SessionStart warning line ("" when current), failing open but saying so."""
    try:
        stale = stale_session_code(directory, ref)
    except Exception as exc:  # the hook must never fail a session
        return f"session-roles: the session-code freshness check failed ({type(exc).__name__}); not verified."
    if stale is None:
        return f"session-roles: could not verify session-code freshness (no {ref} here; `git fetch origin` first)."
    if not stale:
        return ""
    shown = ", ".join(stale[:4]) + (f" and {len(stale) - 4} more" if len(stale) > 4 else "")
    return (f"session-roles: STALE SESSION CODE: {len(stale)} file(s) changed on {ref} are missing from this worktree "
            f"({shown}), so this hook may inject the wrong role or handover note. Sync this worktree to {ref}.")


MONITORING_HOOK = "post_tool_hook.py"


def monitoring_hook_loaded(directory: Path | str) -> bool | None:
    """Whether this worktree's project settings register the PostToolUse monitoring hook (`post_tool_hook.py`): True or False,
    `None` when that cannot be told (not a repo, settings present but unparseable). `.claude/settings.local.json` counts too.
    A missing `.claude/settings.json` is False: no project hooks load from here."""
    directory = Path(directory)
    top = _git(["rev-parse", "--show-toplevel"], directory) if directory.is_dir() else None
    if top is None or top.returncode != 0:
        return None
    root = Path(top.stdout.strip())
    commands: set[str] = set()
    for name in (SETTINGS, ".claude/settings.local.json"):
        path = root / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        commands |= _hook_commands(data)
    return any(c.startswith("PostToolUse: ") and MONITORING_HOOK in c for c in commands)


def monitoring_hook_line(directory: Path | str) -> str:
    """The one SessionStart line when the monitoring hook is not loaded here ("" when it is or cannot be told). Report-only; never raises
    (TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH)."""
    try:
        loaded = monitoring_hook_loaded(directory)
    except Exception:  # the hook must never fail a session
        return ""
    if loaded is not False:
        return ""
    return (f"session-roles: the PostToolUse monitoring hook ({MONITORING_HOOK}) is not in this worktree's {SETTINGS}, so this "
            f"session's tool calls will not be recorded. Sync this worktree to origin/main.")


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
