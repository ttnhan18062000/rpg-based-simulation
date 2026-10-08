#!/usr/bin/env python3
"""Launch a session role: `python3 tools/sessions/launch.py <role-or-instance> [--resume] [--dry-run]`.

Plan sections 5, 6.1 and 8 (TCK-20261004-SESSION-LAYER-M2C). Resolves the role from the manifest, makes sure its
worktree exists (self-heal from the role's own branch, never from scratch), looks at the role's runtime state
(`tools/sessions/state.py`) and then:

    live instance      refuse and say so (a second launch of a live role is the failure this prevents)
    released / none    start fresh
    orphaned           NEVER start or resume silently: print the evidence and offer resume / replace / inspect

and finally `exec claude --name <instance> --agent session-<role>` with `SESSION_ROLE=<instance>` (one input
signal for the SessionStart hook, not the root of identity). Resume is always by SESSION ID, never by name (M0m).

`<instance>` is the role id, or `<role>-N` for the Nth holder of a role whose `max_sessions` allows it.
Non-interactive runs never choose for the owner: they print the evidence and exit 3 asking for `--action`.
`--dry-run` prints the exact command and environment without executing anything.

An `cc` shell alias is documented in docs/guides/agent_session_reset_boundaries.md; installing it is the owner's step.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from tools.handover_home import handover_base  # noqa: E402

from tools.sessions import state as st  # noqa: E402
from tools.sessions.resolve import instance_ids  # noqa: E402
from tools.sessions.roster import Role, Roster, load_roster  # noqa: E402
from tools.sessions import settings_freshness as sf  # noqa: E402

EXIT_USAGE, EXIT_REFUSED, EXIT_NEEDS_CHOICE = 2, 4, 3
GIT_OPERATIONS = (
    ("rebase-merge", "a rebase"), ("rebase-apply", "a rebase/am"), ("MERGE_HEAD", "a merge"),
    ("CHERRY_PICK_HEAD", "a cherry-pick"), ("REVERT_HEAD", "a revert"), ("BISECT_LOG", "a bisect"),
)
HANDOVER_STUB = """# Handover — {role}
Updated: {date}

## Open
- (new role: nothing in flight)

## Branch / PR
- Branch: none · PR: none

## Pending user decisions
- none

## Awaiting
- none

## Next
- (first task from the user)
"""


@dataclass(frozen=True)
class Target:
    role: Role
    instance: str  # the role id, or `<role>-N`


@dataclass(frozen=True)
class Transcript:
    session_id: str
    path: Path
    mtime: float


def _run(cmd: list[str], cwd: Path | str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=None if cwd is None else str(cwd), capture_output=True, text=True, timeout=30)


def roster_listing(roster: Roster) -> str:
    return "\n".join(f"  {r.role}  ({r.seat_status}, max_sessions {r.max_sessions})" for r in roster.roles)


def resolve_target(name: str, roster: Roster) -> Target | None:
    for r in roster.roles:
        if name in instance_ids(r.role, r.max_sessions):
            return Target(r, name)
    return None


# ---- the claude command ------------------------------------------------------------------------

def agent_name(role: Role) -> str:
    return f"session-{role.role}"


def build_command(target: Target, resume_session: str | None = None) -> tuple[list[str], dict[str, str]]:
    cmd = ["claude"]
    if resume_session:
        cmd += ["--resume", resume_session]
    cmd += ["--name", target.instance, "--agent", agent_name(target.role)]
    return cmd, {"SESSION_ROLE": target.instance}


def preflight(worktree: Path, allow_stale: bool) -> tuple[bool, list[str]]:
    """(go, lines): refuse a worktree outside the repo or behind origin/main (TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS).

    A missing directory is skipped (self-heal creates it); an unverifiable ref only warns, so an offline launch still works."""
    if not worktree.is_dir():
        return True, []
    report = sf.check(worktree)
    if report.status == sf.OK:
        return True, []
    if report.status == sf.UNKNOWN or allow_stale and report.inside_repo:
        return True, report.lines() + ["continuing: " + ("freshness could not be verified" if report.status == sf.UNKNOWN else "--allow-stale")]
    return False, report.lines() + ["refusing to launch: this session would run without the project hooks and agent types "
                                     "(sync the worktree from its own branch, or pass --allow-stale)"]


def agent_file_exists(role: Role, root: Path = _REPO_ROOT) -> bool:
    return (root / ".claude" / "agents" / f"{agent_name(role)}.md").is_file()


# ---- worktrees ---------------------------------------------------------------------------------

def default_worktree_path(role: Role, main_checkout: Path) -> Path:
    return main_checkout / ".claude" / "worktrees" / role.worktree


def main_checkout(cwd: Path | str = ".") -> Path:
    return st.common_dir(cwd).parent


def _worktree_entries(cwd: Path) -> list[dict]:
    out = _run(["git", "worktree", "list", "--porcelain"], cwd)
    entries, cur = [], {}
    for line in out.stdout.splitlines() + [""]:
        if not line.strip():
            if cur:
                entries.append(cur)
            cur = {}
            continue
        key, _, val = line.partition(" ")
        cur[key] = val or True
    return entries


_TOPIC = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_DATE_OR_PHASE = re.compile(r"\d{6,8}|(?:^|-)(?:phase|p)-?\d")


def topic_problem(topic: str) -> str | None:
    """Why a `--branch` topic is refused (kebab-case words; no dates or phase numbers), or None."""
    if not _TOPIC.match(topic):
        return "the topic must be lowercase kebab-case words"
    if _DATE_OR_PHASE.search(topic):
        return "the topic must not contain a date or a phase number"
    return None


def bootstrap_worktree(path: Path, role: Role, topic: str, cwd: Path, apply: bool, notes: list[str]) -> list[str]:
    """First-launch / spent-branch path: `git worktree add <path> -b <role>-<topic> origin/main`, only on an explicit topic."""
    problem = topic_problem(topic)
    if problem:
        return notes + [f"--branch {topic!r} refused: {problem}"]
    new = f"{role.role}-{topic}"
    if _run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{new}"], cwd).returncode == 0:
        return notes + [f"branch `{new}` already exists: pick another --branch topic (nothing is reused or reset)"]
    cmd = ["git", "worktree", "add", str(path), "-b", new, "origin/main"]
    if not apply:
        return notes + ["would run: " + " ".join(cmd)]
    _run(["git", "worktree", "prune"], cwd)
    res = _run(cmd, cwd)
    if res.returncode != 0:
        return notes + [f"creating it failed: {res.stderr.strip()}"]
    return notes + [f"created {path} on new branch `{new}` from origin/main"]


def branch_spent_reason(branch: str, cwd: Path) -> str | None:
    """Why a recorded branch is spent (merged), or None. PRs here are squash-merged, so the branch is usually NOT an
    ancestor of origin/main: also ask for a merged PR (`gh`), and if gh fails fall back to `git cherry` showing
    nothing unmerged."""
    if _run(["git", "merge-base", "--is-ancestor", f"refs/heads/{branch}", "origin/main"], cwd).returncode == 0:
        return "is merged into origin/main"
    try:
        res = _run(["gh", "pr", "list", "--head", branch, "--state", "merged", "--json", "number"], cwd)
        if res.returncode == 0:
            return "has a merged PR" if json.loads(res.stdout or "[]") else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    cherry = _run(["git", "cherry", "origin/main", f"refs/heads/{branch}"], cwd)
    if cherry.returncode == 0 and not any(line.startswith("+") for line in cherry.stdout.splitlines()):
        return "has no commit missing from origin/main (squash-merged)"
    return None


def ensure_worktree(path: Path, branch: str | None, cwd: Path, apply: bool = True,
                    role: Role | None = None, topic: str | None = None) -> list[str]:
    """Self-heal a missing or prunable worktree from the role's branch; returns what was said/done.

    Never from scratch: with no recorded branch, a branch git no longer has, or a branch already merged into
    origin/main, it reports and stops.
    Commits live in the shared object store, so only uncommitted files of a removed worktree are lost,
    and that is stated."""
    entries = _worktree_entries(cwd)
    known = next((e for e in entries if Path(e.get("worktree", "")).resolve() == path.resolve()), None)
    if known and path.is_dir() and "prunable" not in known:
        return []
    notes = [f"worktree {path} is missing or prunable"]
    if topic and role:  # an explicit --branch always wins over whatever branch is recorded
        why = [f"recorded branch `{branch}` is not reused: --branch was given"] if branch else []
        return bootstrap_worktree(path, role, topic, cwd, apply, notes + why)
    if not branch:
        return notes + ["no branch is recorded for this role, so it is not recreated: pass `--branch <topic>` to create "
                        "`<role>-<topic>` from origin/main, or create the worktree yourself "
                        "(`git worktree add <path> <branch>`) and relaunch"]
    if _run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd).returncode != 0:
        return notes + [f"the role's branch `{branch}` no longer exists: nothing is invented; restore it from the "
                        "branch-backup file or choose a branch, then relaunch"]
    spent = branch_spent_reason(branch, cwd)
    if spent:
        return notes + [f"recorded branch `{branch}` {spent}: not recreated from a spent branch; pass `--branch <topic>` "
                        "to create `<role>-<topic>` from origin/main, or create the worktree from origin/main yourself "
                        "(`git worktree add <path> -b <new-branch> origin/main`) and relaunch"]
    if not apply:
        return notes + [f"would run: git worktree prune; git worktree add {path} {branch}"]
    _run(["git", "worktree", "prune"], cwd)
    res = _run(["git", "worktree", "add", str(path), branch], cwd)
    if res.returncode != 0:
        return notes + [f"recreating it failed: {res.stderr.strip()}"]
    return notes + [f"recreated {path} from branch `{branch}`; any UNCOMMITTED files of the removed worktree are gone"]


# ---- evidence for an orphan --------------------------------------------------------------------

def projects_dir() -> Path:
    return Path.home() / ".claude" / "projects"


def find_transcript(session_id: str, pdir: Path) -> Transcript | None:
    """By session id, across every project directory: the payload path is only a hint (M0p)."""
    for p in sorted(pdir.glob(f"*/{session_id}.jsonl")):
        return Transcript(session_id, p, p.stat().st_mtime)
    return None


def find_transcripts(title: str | Iterable[str], pdir: Path) -> list[Transcript]:
    """Candidate transcripts of a role: every project dir scanned for `customTitle` equal to one of the titles
    (the instance id, plus the seat's legacy session name for its first instance), newest first."""
    titles = {title} if isinstance(title, str) else set(title)
    found = []
    for p in pdir.glob("*/*.jsonl"):
        try:
            with p.open(encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if "customTitle" in line and any(t in line for t in titles):
                        try:
                            if json.loads(line).get("customTitle") in titles:
                                found.append(Transcript(p.stem, p, p.stat().st_mtime))
                                break
                        except ValueError:
                            continue
        except OSError:
            continue
    return sorted(found, key=lambda t: -t.mtime)


def candidate_titles(target: Target) -> tuple[str, ...]:
    """The titles a role's transcripts may carry: its instance id, and, for the first instance only, the seat's
    `legacy_session_name` (a live seat titled before the instance-id naming, recorded in the registry)."""
    legacy = target.role.legacy_session_name
    if legacy and target.instance == target.role.role and legacy != target.instance:
        return (target.instance, legacy)
    return (target.instance,)


def git_operation_in_progress(worktree: Path) -> list[str]:
    out = []
    for marker, label in GIT_OPERATIONS:
        res = _run(["git", "rev-parse", "--git-path", marker], worktree)
        if res.returncode == 0:
            path = Path(res.stdout.strip())
            path = path if path.is_absolute() else worktree / path
            if path.exists():
                out.append(label)
    return out


def _age(seconds: float) -> str:
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    return f"{seconds / 3600:.1f}h" if seconds < 172800 else f"{seconds / 86400:.1f}d"


def handover_summary(path: Path) -> tuple[float | None, str]:
    if not path.is_file():
        return None, "no handover note"
    awaiting = ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("## awaiting"):
            awaiting = next((x.strip() for x in lines[i + 1:] if x.strip() and not x.startswith("##")), "")
            break
    return path.stat().st_mtime, awaiting or "(no Awaiting section)"


def gather_evidence(target: Target, instance: st.Instance, worktree: Path, handover: Path, pdir: Path,
                    now: float | None = None) -> tuple[list[str], list[Transcript], float | None]:
    """Everything the owner needs to pick resume / replace / inspect. Returns (lines, candidates, handover mtime)."""
    now = now if now is not None else time.time()
    holder = instance.holder
    lines = [f"role {target.instance} is ORPHANED: its recorded process is gone and it did not end cleanly."]
    own = find_transcript(holder.session_id, pdir)
    lines.append(f"  last holder session {holder.session_id}, started {holder.ts}" +
                 (f"; transcript last written {_age(now - own.mtime)} ago" if own else "; transcript not found"))
    lines.append(f"  worktree {holder.worktree} on `{holder.branch or '?'}`")
    if worktree.is_dir():
        dirty = _run(["git", "status", "--porcelain"], worktree).stdout.splitlines()
        lines.append(f"  dirty files: {len(dirty)}")
        ahead = _run(["git", "log", "--oneline", "@{u}..HEAD"], worktree)
        lines.append("  unpushed commits: " + (str(len(ahead.stdout.splitlines())) if ahead.returncode == 0 else "unknown (no upstream)"))
        ops = git_operation_in_progress(worktree)
        if ops:
            lines.append(f"  GIT OPERATION LEFT IN PROGRESS: {', '.join(ops)}. This is a NEVER-boundary state "
                         "(docs/guides/agent_session_reset_boundaries.md): resolve it before anything else.")
        pr = _run(["gh", "pr", "list", "--head", holder.branch, "--json", "number,title,state"], worktree) if holder.branch else None
        if pr is not None and pr.returncode == 0:
            lines.append(f"  open PR: {pr.stdout.strip() or '[]'}")
        else:
            lines.append("  open PR: unknown (gh unavailable or no branch)")
    else:
        lines.append("  the worktree directory does not exist (see the self-heal note)")
    h_mtime, awaiting = handover_summary(handover)
    lines.append(f"  handover note: {'age ' + _age(now - h_mtime) if h_mtime else 'none'}; awaiting: {awaiting}")
    titles = candidate_titles(target)
    cands = find_transcripts(titles, pdir)
    lines.append(f"  candidate transcripts (customTitle in {', '.join(titles)}, newest first): {len(cands)}")
    for t in cands[:5]:
        lines.append(f"    {t.session_id}  {_age(now - t.mtime)} ago  {t.path}")
    return lines, cands, h_mtime


def default_action(own: Transcript | None, handover_mtime: float | None) -> str:
    """Resume only the dead holder's OWN session, and only when its transcript is newer than the handover note
    (plan 6.1). Never the newest transcript titled with the role: that may be a different, live session of the
    same role (found in the 2026-10-04 live rehearsal, where it was the operator's own session)."""
    if own is not None and (handover_mtime is None or own.mtime > handover_mtime):
        return "resume"
    return "replace"


# ---- main --------------------------------------------------------------------------------------

def plan_launch(target: Target, root: Path, state_root: Path, worktree: Path, pdir: Path, action: str | None,
                session_id: str | None, interactive: bool, resume_flag: bool, input_fn=input) -> tuple[int, list[str], str | None]:
    """Decide what to do. Returns (exit code, lines to print, session id to resume or None). Exit 0 = go."""
    instance = st.read_instance(state_root, target.instance)
    handover = handover_base(root) / target.role.handover
    if instance is None or st.liveness(instance) == st.RELEASED:
        stub = [] if handover.is_file() else ["no handover note yet: a stub will be created"]
        return 0, stub, None
    state = st.liveness(instance)
    if state == st.LIVE:
        h = instance.holder
        return EXIT_REFUSED, [f"role {target.instance} is LIVE (session {h.session_id}, pid {h.process.pid if h.process else '?'}): "
                              "refusing a second launch. Use that session, or end it first."], None
    evidence, cands, h_mtime = gather_evidence(target, instance, worktree, handover, pdir)
    own = find_transcript(instance.holder.session_id, pdir)
    chosen = action
    if chosen is None:
        suggested = default_action(own, h_mtime)
        if not interactive:
            return EXIT_NEEDS_CHOICE, evidence + [f"non-interactive: not choosing for you. Rerun with --action resume|replace|inspect "
                                                 f"(suggested: {suggested})."], None
        evidence.append(f"Choose: resume / replace / inspect [{suggested}]")
        answer = input_fn("\n".join(evidence) + "\n> ").strip().lower() or suggested
        chosen, evidence = answer, []
    if chosen not in ("resume", "replace", "inspect"):
        return EXIT_USAGE, evidence + [f"unknown action {chosen!r}"], None
    if chosen == "inspect":
        return EXIT_NEEDS_CHOICE, evidence or ["(evidence printed above)"], None
    if chosen == "resume":
        if session_id is None and own is None:
            return EXIT_NEEDS_CHOICE, evidence + [
                "cannot resume: the dead holder never wrote a transcript (it ended before its first turn). The "
                "candidates above are other sessions of this role, possibly live; pass --session-id <id> to pick one "
                "explicitly, or --action replace."], None
        sid = session_id or instance.holder.session_id
        return 0, evidence + [f"resuming session {sid} (by id, never by name)"], sid
    return 0, evidence + ["replacing: a fresh instance reads the handover note and the git state; the old transcript is kept"], None


def disk_warning(root: Path) -> list[str]:
    """One warning line when free space is below the threshold, else nothing. Warns only: any failure
    here yields no line, never a changed exit code. The tree walk runs only when the cheap free-space
    reading is already low (a walk of ~50 worktrees is slow)."""
    try:
        from tools.sessions import disk_headroom as dh

        limit = dh.threshold_bytes()
        if dh.low_space_line(dh.free_bytes(root), limit) is None:
            return []
        line = dh.warning_line(dh.measure(root), limit) or dh.low_space_line(dh.free_bytes(root), limit)
        return [line] if line else []
    except Exception:
        return []


def main(argv: list[str] | None = None, root: Path = _REPO_ROOT) -> int:
    ap = argparse.ArgumentParser(description="Launch a session role.")
    ap.add_argument("role")
    ap.add_argument("--resume", action="store_true", help="continue the role's latest session (same as --action resume)")
    ap.add_argument("--action", choices=("resume", "replace", "inspect"))
    ap.add_argument("--session-id", help="resume exactly this session id")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-stale", action="store_true", help="launch although the worktree's settings/agents differ from origin/main")
    ap.add_argument("--branch", help="topic for a NEW branch `<role>-<topic>` cut from origin/main when the role's worktree is "
                    "missing and no usable branch is recorded (never created without it)")
    ap.add_argument("--worktree", help="physical worktree path (default: <main checkout>/.claude/worktrees/<name>)")
    a = ap.parse_args(argv)
    roster = load_roster(root)
    target = resolve_target(a.role, roster)
    if target is None:
        print(f"unknown role {a.role!r}. Roles:\n{roster_listing(roster)}", file=sys.stderr)
        return EXIT_USAGE
    role = target.role
    if role.seat_status != "staffed":
        print(f"note: seat `{role.role}` is unstaffed (interim holder: {role.interim_holder}).")
    if not agent_file_exists(role, root):
        print(f"missing .claude/agents/{agent_name(role)}.md (run tools/sessions/generate_agents.py)", file=sys.stderr)
        return EXIT_USAGE
    try:
        sroot = st.state_root(root)
        wt = Path(a.worktree) if a.worktree else default_worktree_path(role, main_checkout(root))
        recorded = st.read_instance(sroot, target.instance)
        for line in ensure_worktree(wt, recorded.holder.branch if recorded else None, root, apply=not a.dry_run,
                                  role=role, topic=a.branch):
            print(line)
        code, lines, sid = plan_launch(target, root, sroot, wt, projects_dir(), a.action or ("resume" if a.resume and recorded else None),
                                       a.session_id, sys.stdin.isatty() and sys.stdout.isatty(), a.resume)
    except st.StateError as exc:
        print(f"state: {exc}", file=sys.stderr)
        return EXIT_USAGE
    for line in lines:
        print(line)
    if code != 0:
        return code
    go, notes = preflight(wt, a.allow_stale)
    for line in notes:
        print(line)
    if not go:
        return EXIT_REFUSED
    for line in disk_warning(root):
        print(line)
    cmd, env = build_command(target, sid)
    if a.dry_run:
        note = handover_base(root) / role.handover
        print(f"handover note: {note if note.is_file() else 'none'} (read from the main checkout, not the role's worktree)")
        print("DRY RUN: " + " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items()) + " " + " ".join(shlex.quote(c) for c in cmd)
              + f"   (cwd {wt})")
        return 0
    handover = handover_base(root) / role.handover
    if not handover.is_file():
        handover.parent.mkdir(parents=True, exist_ok=True)
        handover.write_text(HANDOVER_STUB.format(role=target.instance, date=time.strftime("%Y-%m-%d")), encoding="utf-8")
    os.chdir(wt)
    os.execvpe(cmd[0], cmd, {**os.environ, **env})
    return 0  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
