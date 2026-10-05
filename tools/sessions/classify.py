"""Pure classifier for the role-conditional PreToolUse guard (`tools/sessions/guard.py`).

TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK. Plan: docs/plans/agent_infrastructure/
session_layer_working_process.md section 10. No I/O: a tool call goes in, a set of authority-class actions
and an `uncertain` flag come out. Deciding what to do about them (deny, ask, allow) is the guard's job,
because that depends on the caller's role.

Action names reuse `registries/session_authority.yaml`'s: commit, push, open_pr, merge,
delete_remote_branch, governing_file_edit, plus `authority_file_edit` (a role must not rewrite the policy that
constrains it). `delete_worktree_or_data` and `workflow_run` are deliberately not classified here: the
Bash-visible deletes are covered by the M5A permission rules, and the Workflow tool is not Bash/Edit/Write.

Uncertainty is never silently allowed: a command that partly matches an authority pattern, or hides it behind
shell indirection (`eval`, `bash -c`, a variable-expanded `git`/`gh`, command substitution), is flagged.
This is a guardrail against mistakes, not a sandbox (plan section 10 threat model).
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass

COMMIT, PUSH, OPEN_PR, MERGE = "commit", "push", "open_pr", "merge"
DELETE_REMOTE_BRANCH = "delete_remote_branch"
GOVERNING_FILE_EDIT, AUTHORITY_FILE_EDIT = "governing_file_edit", "authority_file_edit"

AUTHORITY_FILE = "registries/session_authority.yaml"
GOVERNING_FILES = ("CLAUDE.md", ".claude/settings.json", ".claude/settings.local.json")
GOVERNING_DIR_MARKERS = ("/hooks/", ".claude/hooks/")

_EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
_READ_ONLY_VERBS = frozenset({"cat", "head", "tail", "grep", "rg", "ls", "wc", "diff", "stat", "less", "file"})
_READ_ONLY_GIT = frozenset({"diff", "log", "show", "blame", "status", "ls-files", "grep", "cat-file"})
_GIT_OPTS_WITH_ARG = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"})
_SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=\S*$")
_INDIRECTION = re.compile(
    r"(?:^|[\s;&|(])(?:eval|(?:ba|z|da)?sh\s+-\w*c|xargs\s+(?:git|gh))\b"
    r"|\$\{?[A-Za-z_]\w*\}?\s+(?:push|commit|pr\b|api\b)"
    r"|(?:\$\(|`)[^)`]*\b(?:git|gh)\b"
)
_AUTHORITY_WORDS = re.compile(r"\b(?:push|commit|merge|delete|pr\s+(?:create|merge))\b|--force|session_authority|settings\.json|CLAUDE\.md")


@dataclass(frozen=True)
class Classification:
    actions: frozenset[str]
    uncertain: bool = False
    detail: str = ""

    @property
    def is_authority(self) -> bool:
        return bool(self.actions) or self.uncertain


NONE = Classification(frozenset())


def classify(tool_name: str, tool_input: dict) -> Classification:
    """Classify one tool call. Never reads files or state."""
    if tool_name == "Bash":
        return classify_command(str((tool_input or {}).get("command", "")))
    if tool_name in _EDIT_TOOLS:
        path = (tool_input or {}).get("file_path") or (tool_input or {}).get("notebook_path") or ""
        return classify_path(str(path))
    return NONE


def classify_path(path: str) -> Classification:
    norm = path.replace("\\", "/")
    if norm == AUTHORITY_FILE or norm.endswith("/" + AUTHORITY_FILE):
        return Classification(frozenset({AUTHORITY_FILE_EDIT}), detail=f"edit of {AUTHORITY_FILE}")
    if any(norm == f or norm.endswith("/" + f) for f in GOVERNING_FILES) or any(m in norm for m in GOVERNING_DIR_MARKERS):
        return Classification(frozenset({GOVERNING_FILE_EDIT}), detail=f"edit of governing file {norm}")
    return NONE


def _tokens(segment: str) -> list[str] | None:
    try:
        tokens = shlex.split(segment, posix=True)
    except ValueError:
        return None
    while tokens and _ASSIGNMENT.match(tokens[0]):
        tokens = tokens[1:]
    return tokens


def _git_subcommand(tokens: list[str]) -> tuple[str | None, list[str]]:
    """The git subcommand and its arguments, skipping global options (`-C path`, `-c k=v`, `--no-pager`)."""
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok in _GIT_OPTS_WITH_ARG:
            i += 2
        elif tok.startswith("-"):
            i += 1
        else:
            return tok, tokens[i + 1:]
    return None, []


def _is_delete_push(args: list[str]) -> bool:
    for a in args:
        if a in ("--delete", "-d") or (a.startswith(":") and len(a) > 1):
            return True
    return False


def _segment_actions(tokens: list[str]) -> set[str]:
    if not tokens:
        return set()
    verb = tokens[0].rsplit("/", 1)[-1]
    if verb == "git":
        sub, args = _git_subcommand(tokens)
        if sub == "commit":
            return {COMMIT}
        if sub == "push":
            return {PUSH, DELETE_REMOTE_BRANCH} if _is_delete_push(args) else {PUSH}
        return set()
    if verb == "gh":
        rest = [t for t in tokens[1:] if not t.startswith("-")]
        if rest[:2] == ["pr", "create"]:
            return {OPEN_PR}
        if rest[:2] == ["pr", "merge"]:
            return {MERGE}
        if rest[:1] == ["api"]:
            joined = " ".join(tokens)
            if re.search(r"(?:-X|--method)[ =]DELETE\b", joined, re.IGNORECASE):
                return {DELETE_REMOTE_BRANCH}
    return set()


def _is_read_only(tokens: list[str]) -> bool:
    if not tokens:
        return True
    verb = tokens[0].rsplit("/", 1)[-1]
    if verb in _READ_ONLY_VERBS:
        return True
    if verb == "git":
        sub, _ = _git_subcommand(tokens)
        return sub in _READ_ONLY_GIT
    return False


def classify_command(command: str) -> Classification:
    """Classify a Bash command, splitting compound commands and checking every segment."""
    actions: set[str] = set()
    details: list[str] = []
    uncertain = False
    mentions_governed = any(f in command for f in (AUTHORITY_FILE, *GOVERNING_FILES))

    if _INDIRECTION.search(command) and _AUTHORITY_WORDS.search(command):
        uncertain = True
        details.append("shell indirection around an authority-class word")

    for segment in _SEGMENT_SPLIT.split(command):
        if not segment.strip():
            continue
        tokens = _tokens(segment)
        if tokens is None:
            if _AUTHORITY_WORDS.search(segment):
                uncertain = True
                details.append("unparseable command containing an authority-class word")
            continue
        actions |= _segment_actions(tokens)
        if mentions_governed and not _is_read_only(tokens):
            seg = segment
            if AUTHORITY_FILE in seg:
                actions.add(AUTHORITY_FILE_EDIT)
                details.append(f"non-read-only command touching {AUTHORITY_FILE}")
            if any(f in seg for f in GOVERNING_FILES):
                actions.add(GOVERNING_FILE_EDIT)
                details.append("non-read-only command touching a governing file")

    if DELETE_REMOTE_BRANCH in actions:
        details.append("remote branch deletion")
    return Classification(frozenset(actions), uncertain, "; ".join(dict.fromkeys(details)))
