#!/usr/bin/env python3
"""Role-conditional PreToolUse guard for authority-class operations.

TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK. Plan: docs/plans/agent_infrastructure/
session_layer_working_process.md section 10. `tools/sessions/classify.py` says what a tool call is; this script
adds the part that depends on WHO is calling: the caller's role (from the session binding record), the
function's authority (`registries/session_authority.yaml`) and the worktree's writer lease.

Decision, per action, most severe wins (deny > ask > allow):
  1. the role's function lists the action as `forbidden`          -> deny
  2. commit/push/open_pr in a worktree whose writer lease belongs to ANOTHER role -> deny. No lease at all is not
     a reason to ask (TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED): sessions started outside the role launcher
     never get one
  3. the action is in `needs_user`: merge, a push to the default branch (`push_default_branch`, from an explicit
     refspec or, for a bare `git push`, the cwd's current branch) and remote-branch deletion are ask for every role
     (a grant never overrides them); `workflow_run` and `delete_worktree_or_data` ask unless a grant covers them.
     Owner rule, 2026-10-07 ("Drop all but critical"): the guard asks only about those critical actions. A commit on
     the default branch, governing-file and authority-file edits and an uncertain commit are allowed (governing
     files are protected by review and PR merge). Owner rule, 2026-10-06: "only block the merge branch to main,
     every action on their own branch is allowed"
  4. an uncertain classification asks only when the action set includes push, merge or delete_remote_branch, or the
     raw command text names push, a PR merge, a delete or a worktree removal (`critical_text`, the deliberate
     residual fail-closed); a push whose target branch cannot be determined asks too; any other uncertain command
     is allowed
  5. otherwise allow (exit 0, no output)
An unresolved role (a plain `claude` session) is not role-governed in v1: ask when a critical action is present,
allow the rest.

FAIL-CLOSED DISCIPLINE (M0n, observed 2026-10-03, positive controls included): a PreToolUse call is blocked only
by exit code 2 or a well-formed JSON deny; exit 1 (an uncaught traceback) and unparseable output let the call
RUN. So this script never lets an exception escape: any exception on a payload that mentions an authority word
exits 2 with a message, and a non-authority payload exits 0 whatever happens. Repo imports sit in a module-level
try so a broken import is also a caught failure, not an exit-1 crash.

This is a guardrail against mistakes, not a sandbox (plan section 10 threat model).

WIRING HAZARD: `python3 tools/sessions/guard.py` exits 2 when this file is missing, and exit 2 blocks the tool
call, so the settings.json command must treat a missing script as a pass, e.g.
`test -f tools/sessions/guard.py || exit 0; python3 tools/sessions/guard.py`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from tools.sessions import boundary as bd
    from tools.sessions import classify as cl
    from tools.sessions import state as st
    from tools.sessions.resolve import AGENT_PREFIX
    from tools.sessions.roster import load_authority, load_roster

    _IMPORT_ERROR: Exception | None = None
except Exception as _exc:  # noqa: BLE001 - a broken import must become a caught failure, never an exit-1 crash
    _IMPORT_ERROR = _exc

DENY, ASK = "deny", "ask"
# Needing the user always wins over a grant (plan section 10).
_ALWAYS_ASK = frozenset({"merge", "push_default_branch", "delete_remote_branch"})
# The only actions the guard asks about (owner, 2026-10-07): `workflow_run` and `delete_worktree_or_data` come from a
# function's `needs_user`; `workflow_run` is CLAUDE.md's explicit opt-in.
_CRITICAL = _ALWAYS_ASK | frozenset({"workflow_run", "delete_worktree_or_data"})
_UNCERTAIN_ASKS = frozenset({"push", "merge", "delete_remote_branch"})
# Residual fail-closed (planner, 2026-10-07): an UNCERTAIN command (shell indirection, unparseable text) whose raw text
# names a critical operation still asks even when no action could be parsed out of it. Deliberately narrow: no
# commit, no governing-file names.
_CRITICAL_TEXT = re.compile(r"\bpush\b|\bpr\s+merge\b|--delete|-X\s*DELETE|--method\s+DELETE|\bworktree\s+remove\b")


def critical_text(command: str) -> bool:
    """Whether a raw command text names push, a PR merge, a delete or a worktree removal (`merge` counts only with `gh`)."""
    return bool(_CRITICAL_TEXT.search(command) or (re.search(r"\bmerge\b", command) and re.search(r"\bgh\b", command)))
_WRITER_ACTIONS = frozenset({"commit", "push", "open_pr"})
_EDIT_TOOL_NAMES = ("Edit", "Write", "MultiEdit", "NotebookEdit")  # kept local: `cl` may have failed to import
_AUTHORITY_TEXT = re.compile(
    r"\bgit\b|\bgh\b|eval|xargs|\bsh\b|\bbash\b|\bzsh\b|\$|`|session_authority|settings|CLAUDE\.md|hooks/"
)


@dataclass(frozen=True)
class Caller:
    resolved: bool
    instance: str | None = None
    role_id: str | None = None
    function: str | None = None
    source: str = "none"


def _git_toplevel(cwd: str) -> str:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True, timeout=10)
    return out.stdout.strip() if out.returncode == 0 else ""


def _base_role(instance: str, roster) -> str | None:
    if roster.role(instance):
        return instance
    head, _, tail = instance.rpartition("-")
    return head if tail.isdigit() and roster.role(head) else None


def find_session_instance(root: Path, session_id: str) -> str | None:
    """The role instance whose current holder is `session_id`, else the newest binding naming it.

    There is no lookup by session id in state.py, so this scans the role directories. It is only called for a
    payload already classified as authority-class, never on the fast path."""
    if not session_id or not root.is_dir():
        return None
    newest: tuple[str, str] | None = None
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        try:
            inst = st.read_instance(root, entry.name)
            if inst is not None and not inst.released and inst.holder.session_id == session_id:
                return entry.name
            for binding in st.read_bindings(root, entry.name):
                if binding.session_id == session_id and (newest is None or binding.ts > newest[0]):
                    newest = (binding.ts, entry.name)
        except st.StateError:
            continue
    return newest[1] if newest else None


def resolve_caller(payload: dict, roster, root: Path) -> Caller:
    instance = find_session_instance(root, str(payload.get("session_id", "")))
    source = "binding"
    if instance is None:
        agent_type = str(payload.get("agent_type") or "")
        candidate = agent_type[len(AGENT_PREFIX):] if agent_type.startswith(AGENT_PREFIX) else ""
        if candidate and roster.role(candidate):
            instance, source = candidate, "agent_type"
    if instance is None:
        return Caller(resolved=False)
    base = _base_role(instance, roster)
    role = roster.role(base) if base else None
    if role is None:
        return Caller(resolved=False)
    return Caller(True, instance, role.role, role.function, source)


def _git_out(cwd: str, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10)
    return out.stdout.strip() if out.returncode == 0 else ""


def current_branch(cwd: str) -> str:
    """The cwd's checked-out branch; empty for a detached HEAD or a failure."""
    return _git_out(cwd, "symbolic-ref", "--short", "-q", "HEAD")


def effective_cwd(cwd: str, chain: tuple[str, ...]) -> str | None:
    """Where a command that starts with literal `cd` targets actually runs; None if a target is not a directory."""
    current = cwd
    for target in chain:
        path = Path(target).expanduser()
        path = path if path.is_absolute() else Path(current) / path
        current = os.path.normpath(str(path))
        if not os.path.isdir(current):
            return None
    return current


def default_branches(cwd: str) -> tuple[str, ...]:
    """`main` plus whatever `origin/HEAD` names, so a repo whose default differs is protected too."""
    named = _git_out(cwd, "symbolic-ref", "--short", "-q", "refs/remotes/origin/HEAD").removeprefix("origin/")
    return tuple(dict.fromkeys(("main", named))) if named else ("main",)


def decide(classification, caller: Caller, authority, lease_role: str | None, lease_found: bool, on_default: bool | None = False,
           command: str = ""):
    """Pure decision: (DENY | ASK | None, reason). None means allow.

    `on_default` is whether the call's current branch is the default branch: True, False, or None when it could not
    be determined (detached HEAD, git failure). It only matters for a push with no explicit target."""
    if not classification.is_authority:
        return None, ""
    action_set = set(classification.actions)
    uncertain_critical = classification.uncertain and (bool(_UNCERTAIN_ASKS & action_set) or critical_text(command))
    if "push" in action_set and classification.push_implicit and on_default:
        action_set.add("push_default_branch")
    actions = sorted(action_set)
    label = ", ".join(actions) or "an uncertain command"
    if not caller.resolved:
        if _CRITICAL & action_set or uncertain_critical:
            return ASK, f"role not resolved for this session; {label} is a critical operation. {classification.detail}".strip()
        return None, ""

    fa = authority.for_function(caller.function)
    forbidden = set(fa.forbidden) if fa else set()
    needs_user = set(fa.needs_user) if fa else set()
    grants = {a for g in authority.grants_for(caller.role_id) for a in g.actions}
    ask: list[str] = []

    for action in actions:
        if action in forbidden:
            return DENY, f"{caller.role_id} ({caller.function}) must not {action}: it hands drafts to the implementer"
    for action in actions:
        if action in _WRITER_ACTIONS and lease_found and lease_role != caller.instance:
            return DENY, f"{action} refused: this worktree's writer is {lease_role}, not {caller.instance}"
    if on_default is None and "push" in action_set and classification.push_implicit:
        ask.append("the current branch could not be determined, so it cannot be shown not to be the default branch")
    for action in actions:
        if action in _ALWAYS_ASK:
            ask.append(f"{action} needs the user (a grant never overrides this)")
        elif action in needs_user and action not in grants:
            ask.append(f"{action} needs the user's go and {caller.role_id} has no grant for it")
    if uncertain_critical:
        ask.append(f"uncertain classification: {classification.detail}")
    if ask:
        return ASK, "; ".join(dict.fromkeys(ask))
    return None, ""


def _emit(stdout, decision: str, reason: str) -> None:
    stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"session-roles guard: {reason}",
    }}) + "\n")


def _emit_advisory(stdout, text: str) -> None:
    stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": text}}) + "\n")


def _advise(payload: dict, stdout) -> None:
    """M5C advisory `role_boundary` warning for a call the guard let through. Never a decision, never raises."""
    try:
        if _IMPORT_ERROR is not None or str(payload.get("tool_name", "")) not in (*bd.EDIT_TOOLS, bd.MESSAGE_TOOL):
            return
        root = st.state_root(str(payload.get("cwd") or "."))
        roster = load_roster()
        caller = resolve_caller(payload, roster, root)
        text = bd.advise(payload, caller, roster, root)
        if text:
            _emit_advisory(stdout, text)
    except Exception:  # noqa: BLE001 - advisory only: a failure here must not touch the tool call
        return


def _guard(payload: dict, stdout) -> int:
    if _IMPORT_ERROR is not None:
        raise _IMPORT_ERROR
    classification = cl.classify(str(payload.get("tool_name", "")), payload.get("tool_input") or {})
    if not classification.is_authority:
        _advise(payload, stdout)
        return 0
    cwd = str(payload.get("cwd") or ".")
    root = st.state_root(cwd)
    roster, authority = load_roster(), load_authority()
    caller = resolve_caller(payload, roster, root)
    if cl.PUSH in classification.actions:
        defaults = default_branches(cwd)  # origin/HEAD is shared by a clone's worktrees
        if defaults != cl.DEFAULT_BRANCHES:
            classification = cl.classify(str(payload.get("tool_name", "")), payload.get("tool_input") or {}, defaults)
    else:
        defaults = cl.DEFAULT_BRANCHES
    on_default: bool | None = False
    acts_in = effective_cwd(cwd, classification.cd_chain) if classification.cd_chain else cwd
    if cl.COMMIT in classification.actions or (cl.PUSH in classification.actions and classification.push_implicit):
        branch = current_branch(acts_in) if acts_in else ""
        on_default = (branch in defaults) if branch else None
    lease_role, lease_found = None, False
    if caller.resolved and _WRITER_ACTIONS & classification.actions:
        toplevel = _git_toplevel(acts_in or cwd)
        lease = st.read_lease(root, toplevel) if toplevel else None
        lease_role, lease_found = (lease.role if lease else None), lease is not None
    command = str((payload.get("tool_input") or {}).get("command", "")) if payload.get("tool_name") == "Bash" else ""
    decision, reason = decide(classification, caller, authority, lease_role, lease_found, on_default, command)
    if decision is None:
        return 0
    _emit(stdout, decision, reason)
    return 0


def main(stdin=None, stdout=None, stderr=None) -> int:
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    try:
        raw = stdin.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return 0
    except Exception:  # noqa: BLE001 - nothing to classify
        return 0
    tool = ""
    try:
        tool = str(payload.get("tool_name", ""))
        if tool == "Bash" and not _AUTHORITY_TEXT.search(str((payload.get("tool_input") or {}).get("command", ""))):
            return 0  # fast path: nothing that could be an authority-class command
        return _guard(payload, stdout)
    except Exception as exc:  # noqa: BLE001 - fail closed for authority-class input, open otherwise
        if tool in ("Bash", *_EDIT_TOOL_NAMES) and _AUTHORITY_TEXT.search(raw):
            stderr.write(
                f"session-roles guard failed on a call that may be authority-class ({type(exc).__name__}: {exc}); "
                "blocked. Ask the user before retrying.\n"
            )
            return 2
        return 0


if __name__ == "__main__":
    sys.exit(main())
