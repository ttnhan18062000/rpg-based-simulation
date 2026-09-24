#!/usr/bin/env python3
"""Advisory-only `PreToolUse` hook for `Bash`, firing on `git push` (TCK-20260924-DELIVERY-
PRE-PUSH-ADVISORY): says what it checked, never blocks.

Mirrors `tools/agent-monitoring/cd_prefix_advisory_hook.py`'s exact shape (pure detection
functions + a thin stdin-JSON `main()`, wrapped in `try/except: pass`, printing
`hookSpecificOutput.additionalContext` only when there is something to report, always exiting 0).
Lives under `tools/delivery/`, not `tools/agent-monitoring/`, despite following that module's
shape — the epic's own ordering constraint forbids touching `tools/agent-monitoring/` ahead of
`TCK-20260924-DELIVERY-COST-MEASUREMENT`.

**Matcher**: `git push` is measured (over `agent-monitoring/data/2026-W*/tools.jsonl`, 322 real
invocations) to appear overwhelmingly as the *whole* command (77.6%) or the *last* statement in a
chain (newline 19.9%, `&&` 1.6%, `;` 0.9%) — the mirror image of the `cd`-prefix hook's own target
shape, which is why the matcher fires on `git push` at a statement-start position (command start,
or immediately after `&&`/`;`/a newline), not on the substring appearing anywhere. The one
confirmed false-positive shape in the corpus (`git push` inside a `grep` pattern string, e.g. `grep
-n "git commit\\|git push\\|..."`) does not follow any of those three anchors and is excluded by
construction, not by a special case.

Three checks, each read-only against local refs (no network call — an offline-first design so this
hook cannot itself become a source of the Fortiguard TLS-block failure mode this epic elsewhere
defends against):

- **A — commit subjects name a real ticket.** Every commit on the branch ahead of `origin/main`
  should reference a `TCK-` ID that resolves to a real file somewhere under `tickets/` (a ticket
  legitimately moves `inprogress/` -> `done/` during its own branch's life, so the search is
  recursive, not directory-specific).
- **B — the current week's `agent-monitoring/data/YYYY-Www/*.jsonl` shard is staged.** The
  monitoring hooks rewrite it on nearly every tool call, so an unstaged shard at push time is the
  default failure mode, not an unusual one.
- **C — the branch is not a finished, squash-merged one.** Detects the specific shape from
  `docs/guides/delivery_process.md`'s "PR Lifecycle" step 7: commits exist ahead of `origin/main`
  (`git rev-list --count`), `HEAD` is genuinely not an ancestor of `origin/main`
  (`git merge-base --is-ancestor`), the two-ref content diff (`git diff origin/main HEAD`) is
  empty, yet the three-dot ancestor-based diff (`git diff origin/main...HEAD`) is not — the
  reliable discriminator this repo's own CLAUDE.md prose describes, operationalized as code. A
  branch merely behind `main` (no squash-merge involved) fails the ancestor/content conditions and
  is correctly never flagged.

Every check degrades to "no finding" on any git-command failure (detached HEAD, no local
`origin/main` ref, non-tracking branch) rather than raising — this hook must never traceback, and
an uncertain check says nothing, not something wrong.

Out of scope, deliberately: fixing anything found (no auto-staging, no rewriting commit messages,
no branch creation, no history rewrite — report only), any blocking behavior under any
circumstance, and any network call.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, NamedTuple

_GIT_PUSH_RE = re.compile(r"(?:^|&&|;)\s*git\s+push\b", re.MULTILINE)
_TICKET_ID_RE = re.compile(r"TCK-[0-9]{8}-[A-Z0-9-]+")
_DEFAULT_TICKETS_ROOT = Path("tickets")


class CommandResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


def default_run_command(cmd: list, timeout: int = 30) -> CommandResult:
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return CommandResult(1, "", str(exc))


def is_git_push_command(command: str) -> bool:
    return bool(_GIT_PUSH_RE.search(command or ""))


def _find_ticket_file(ticket_id: str, tickets_root: Path) -> bool:
    return next(tickets_root.rglob(f"{ticket_id}.md"), None) is not None


def check_commit_subjects(
    run_command=default_run_command,
    base_ref: str = "origin/main",
    tickets_root: Path = _DEFAULT_TICKETS_ROOT,
) -> List[str]:
    result = run_command(["git", "log", f"{base_ref}..HEAD", "--format=%h\t%s"])
    if result.returncode != 0:
        return []

    findings = []
    for line in result.stdout.splitlines():
        if "\t" not in line:
            continue
        sha, subject = line.split("\t", 1)
        ids = _TICKET_ID_RE.findall(subject)
        if not ids:
            findings.append(f"pre-push: commit {sha} subject names no ticket ID: {subject!r}")
            continue
        for ticket_id in ids:
            if not _find_ticket_file(ticket_id, tickets_root):
                findings.append(
                    f"pre-push: commit {sha} references {ticket_id}, but no ticket file exists "
                    f"anywhere under {tickets_root}/"
                )
    return findings


def _current_iso_week() -> str:
    iso = datetime.now(timezone.utc).isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def check_monitoring_shard_staged(run_command=default_run_command) -> List[str]:
    week = _current_iso_week()
    shard_dir = f"agent-monitoring/data/{week}/"
    result = run_command(["git", "status", "--porcelain", "--", shard_dir])
    if result.returncode != 0:
        return []
    dirty = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not dirty:
        return []
    return [
        f"pre-push: {shard_dir} has dirty/untracked file(s) not staged for this push: "
        f"{'; '.join(dirty)}"
    ]


def check_squash_merged_finished(run_command=default_run_command, base_ref: str = "origin/main") -> List[str]:
    ahead = run_command(["git", "rev-list", "--count", f"{base_ref}..HEAD"])
    if ahead.returncode != 0:
        return []
    try:
        ahead_count = int(ahead.stdout.strip())
    except ValueError:
        return []
    if ahead_count == 0:
        return []

    is_ancestor = run_command(["git", "merge-base", "--is-ancestor", "HEAD", base_ref])
    if is_ancestor.returncode == 0:
        return []  # HEAD is an ancestor of base_ref -- ordinary case, not the finished-branch shape

    two_dot = run_command(["git", "diff", "--shortstat", base_ref, "HEAD"])
    if two_dot.returncode != 0 or two_dot.stdout.strip():
        return []  # fetch failed, or there IS real new content -- not the finished-branch shape

    three_dot = run_command(["git", "diff", "--shortstat", f"{base_ref}...HEAD"])
    if three_dot.returncode != 0 or not three_dot.stdout.strip():
        return []

    return [
        "pre-push: this branch looks squash-merged and finished — its content already matches "
        f"{base_ref} (no real diff), yet its own commits are not ancestors of {base_ref}. "
        "Pushing further commits here has no path to main. Cut a fresh branch off "
        f"{base_ref} for new work; never push further to this one."
    ]


def run_all_checks(
    run_command=default_run_command,
    base_ref: str = "origin/main",
    tickets_root: Path = _DEFAULT_TICKETS_ROOT,
) -> List[str]:
    findings = []
    findings.extend(check_commit_subjects(run_command, base_ref, tickets_root))
    findings.extend(check_monitoring_shard_staged(run_command))
    findings.extend(check_squash_merged_finished(run_command, base_ref))
    return findings


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", payload).get("command", "")
        if not is_git_push_command(command):
            return 0
        findings = run_all_checks()
        if findings:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": "\n".join(findings),
                }
            }))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
