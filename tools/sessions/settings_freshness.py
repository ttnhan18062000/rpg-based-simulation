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

_ROOT = str(Path(__file__).resolve().parents[2])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from tools.agent_working_paths import AGENT_MONITORING  # noqa: E402

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


MONITORING_HOOK = "tools/agent-monitoring/post_tool_hook.py"


def _worktree_root(directory: Path | str) -> Path | None:
    directory = Path(directory)
    top = _git(["rev-parse", "--show-toplevel"], directory) if directory.is_dir() else None
    return Path(top.stdout.strip()) if top is not None and top.returncode == 0 else None


def monitoring_hook_line(directory: Path | str) -> str:
    """TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH: one report-only SessionStart line ("" when the tool-row hook is
    in place) when this worktree would write no tool rows: the PostToolUse monitoring hook is not in its
    `.claude/settings.json`, or its script is missing (the hook command is `test -f <script> || exit 0`, so a missing script
    is silent). Failing open, never a fetch."""
    try:
        root = _worktree_root(directory)
        if root is None:
            return ""
        settings = root / SETTINGS
        wired = False
        if settings.is_file():
            wired = any(MONITORING_HOOK in c for c in _hook_commands(_json(settings.read_text(encoding="utf-8")))
                        if c.startswith("PostToolUse:"))
        problems = []
        if not wired:
            problems.append(f"{SETTINGS} has no PostToolUse hook for {MONITORING_HOOK}")
        if not (root / MONITORING_HOOK).is_file():
            problems.append(f"{MONITORING_HOOK} is missing here")
        if not problems:
            return ""
        return ("monitoring: NO TOOL-ROW HOOK in this worktree, so this session's tool calls will leave no rows: "
                + "; ".join(problems) + ". Sync this worktree to origin/main.")
    except Exception as exc:  # the hook must never fail a session
        return f"monitoring: the tool-row hook check failed ({type(exc).__name__}); not verified."


def unstaged_tool_rows_line(directory: Path | str) -> str:
    """The other half: tool rows this worktree wrote that no commit carries yet. The pre-push advisory only looks at the
    current ISO week's shard directory, so rows left uncommitted in an older week's shard never reach `main` and never
    get flagged. Report-only ("" when nothing is pending); counts the added lines of every dirty or untracked
    `*tools.jsonl` under the monitoring data directory."""
    try:
        root = _worktree_root(directory)
        if root is None:
            return ""
        data = (AGENT_MONITORING / "data").as_posix()
        status = _git(["status", "--porcelain", "--untracked-files=all", "--", data], root)
        if status.returncode != 0:
            return ""
        files = [ln[3:].strip() for ln in status.stdout.splitlines() if ln[3:].strip().endswith("tools.jsonl")]
        if not files:
            return ""
        rows = 0
        for name in files:
            path = root / name
            if path.is_file():
                tracked = _git(["ls-files", "--error-unmatch", name], root).returncode == 0
                if tracked:
                    stat = _git(["diff", "HEAD", "--numstat", "--", name], root)
                    rows += int((stat.stdout.split() or ["0"])[0]) if stat.returncode == 0 and stat.stdout.split()[:1] != ["-"] else 0
                else:
                    rows += sum(1 for _ in path.open("rb"))
        weeks = sorted({Path(f).parent.name for f in files})
        return (f"monitoring: {rows} tool row(s) in {len(files)} shard file(s) ({', '.join(weeks)}) are not in any commit; "
                f"stage `{data}/` in your next commit or they never reach main.")
    except Exception as exc:
        return f"monitoring: the pending tool-row check failed ({type(exc).__name__}); not verified."


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
