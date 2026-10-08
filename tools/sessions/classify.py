"""Pure classifier for the role-conditional PreToolUse guard (`tools/sessions/guard.py`).

TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK. Plan: docs/plans/agent_infrastructure/
session_layer_working_process.md section 10. No I/O: a tool call goes in, a set of authority-class actions
and an `uncertain` flag come out. Deciding what to do about them (deny, ask, allow) is the guard's job,
because that depends on the caller's role.

Action names reuse `registries/session_authority.yaml`'s: commit, push, open_pr, merge,
delete_remote_branch, governing_file_edit, plus `authority_file_edit` (a role must not rewrite the policy that
constrains it) and `push_default_branch` (TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED: a push whose destination is the
default branch; a push to any other branch is a plain `push`). A push with no explicit destination goes to the
current branch, which a pure function cannot know: it is flagged `push_implicit` and the guard resolves the branch. `delete_worktree_or_data` and `workflow_run` are deliberately not classified here: the
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
PUSH_DEFAULT_BRANCH = "push_default_branch"
DEFAULT_BRANCHES = ("main",)
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
_CODE_PAYLOAD = r"(?:^|[\s;&|(])(?:eval|(?:ba|z|da)?sh\s+-\w*c|xargs\s+(?:git|gh))\b"
_INDIRECTION = re.compile(
    _CODE_PAYLOAD
    + r"|\$\{?[A-Za-z_]\w*\}?\s+(?:push|commit|pr\b|api\b)"
    r"|(?:\$\(|`)[^)`]*\b(?:git|gh)\b"
)
_AUTHORITY_WORDS = re.compile(r"\b(?:push|commit|merge|delete|pr\s+(?:create|merge))\b|--force|session_authority|settings\.json|CLAUDE\.md")


_HEREDOC = re.compile(r"<<(?!<)(-?)[ \t]*(?:'(\w+)'|\"(\w+)\"|\\?(\w+))")
_SHELL_FEED = re.compile(r"\b(?:(?:ba|z|da|k)?sh|source|eval)\b")
_CODE_PAYLOAD_RE = re.compile(_CODE_PAYLOAD)
_PLAIN_WORD = re.compile(r"^[\w./:@%+=,~-]*$")


def _strip_heredocs(command: str) -> str:
    """Drop heredoc bodies (`<<EOF`, `<<'EOF'`, `<<-EOF`, through the terminator line): they are data for the command,
    not commands. The line holding `<<` stays (so `cat > CLAUDE.md <<EOF` keeps its write target). A body fed to a shell
    (`bash <<EOF`) is code and stays; so does a heredoc with no terminator line (nothing is assumed)."""
    out: list[str] = []
    pos = 0
    while True:
        m = _HEREDOC.search(command, pos)
        if not m:
            break
        delim = m.group(2) or m.group(3) or m.group(4)
        nl = command.find("\n", m.end())
        line_start = command.rfind("\n", 0, m.start()) + 1
        if nl < 0 or _SHELL_FEED.search(command[line_start:m.start()]):
            out.append(command[pos:m.end()])
            pos = m.end()
            continue
        lines = command[nl + 1:].split("\n")
        for i, line in enumerate(lines):
            if (line.lstrip("\t") if m.group(1) else line) == delim:
                out.append(command[pos:nl + 1])
                rest = "\n".join(lines[i + 1:])
                command, pos = command[:nl + 1] + rest, nl + 1
                break
        else:
            out.append(command[pos:m.end()])
            pos = m.end()
    out.append(command[pos:])
    return "".join(out)


def _substitutions(text: str) -> list[str]:
    """The inner commands of `$(...)` and backtick substitutions in a double-quoted string (they run)."""
    found: list[str] = []
    i = 0
    while i < len(text):
        if text.startswith("$(", i):
            depth, j = 1, i + 2
            while j < len(text) and depth:
                depth += (text[j] == "(") - (text[j] == ")")
                j += 1
            found.append(text[i + 2:j - 1])
            i = j
        elif text[i] == "`":
            j = text.find("`", i + 1)
            j = len(text) if j < 0 else j
            found.append(text[i + 1:j])
            i = j + 1
        else:
            i += 1
    return found


def _strip_quotes(command: str) -> str | None:
    """Replace quoted text strings with `''`, keeping what runs: command substitutions inside double quotes are
    re-emitted as `; <inner> ;`. A quoted plain word (an operand such as `"main"`) stays. None on an unbalanced quote."""
    out: list[str] = []
    i = 0
    while i < len(command):
        c = command[i]
        if c == "\\":
            out.append(command[i:i + 2])
            i += 2
        elif c in "'\"":
            j = i + 1
            while j < len(command) and command[j] != c:
                j += 2 if (c == '"' and command[j] == "\\") else 1
            if j >= len(command):
                return None
            body = command[i + 1:j]
            if _PLAIN_WORD.match(body):
                out.append(command[i:j + 1])
            else:
                out.append("''")
                if c == '"':
                    out.extend(f" ; {sub} ; " for sub in _substitutions(body))
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


def strip_text(command: str) -> str:
    """The command with its data removed (heredoc bodies and quoted text strings), for classifying what is left.

    `eval` / `sh -c` payloads are code, so quoted text is kept when one is present. An unbalanced quote also keeps the
    text (fail closed: the authority-word checks then see the whole command)."""
    text = _strip_heredocs(command)
    if _CODE_PAYLOAD_RE.search(text):
        return text
    stripped = _strip_quotes(text)
    return text if stripped is None else stripped


@dataclass(frozen=True)
class Classification:
    actions: frozenset[str]
    uncertain: bool = False
    detail: str = ""
    push_implicit: bool = False  # a push with no explicit destination: it goes to the call's current branch
    cd_chain: tuple[str, ...] = ()  # literal `cd`/`pushd` targets that precede the first commit/push, in order

    @property
    def is_authority(self) -> bool:
        return bool(self.actions) or self.uncertain


NONE = Classification(frozenset())


def classify(tool_name: str, tool_input: dict, default_branches: tuple[str, ...] = DEFAULT_BRANCHES) -> Classification:
    """Classify one tool call. Never reads files or state."""
    if tool_name == "Bash":
        return classify_command(str((tool_input or {}).get("command", "")), default_branches)
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


_PUSH_OPTS_WITH_ARG = frozenset({"-o", "--push-option", "--repo", "--receive-pack", "--exec"})
_REPO_REDIRECTING_GIT_OPTS = frozenset({"-C", "--git-dir", "--work-tree"})


def _push_destinations(args: list[str]) -> tuple[list[str], bool, bool]:
    """(explicit destination branches, implicit, all_refs) for `git push` arguments.

    `--all`/`--mirror` may include the default branch (all_refs). Refspecs are the positionals after the remote:
    `+src:dst` pushes to dst, a bare `x` to x, and a bare `HEAD` to the current branch (implicit). No refspec means the
    current branch (implicit). `--tags` with no refspec pushes no branch."""
    positionals: list[str] = []
    all_refs = tags_only = False
    skip = False
    for a in args:
        if skip:
            skip = False
        elif a in _PUSH_OPTS_WITH_ARG:
            skip = True
        elif a in ("--all", "--mirror"):
            all_refs = True
        elif a == "--tags":
            tags_only = True
        elif not a.startswith("-"):
            positionals.append(a)
    refspecs = positionals[1:]
    if not refspecs:
        return [], not tags_only, all_refs
    explicit: list[str] = []
    implicit = False
    for spec in refspecs:
        dst = spec.lstrip("+").split(":", 1)[-1]
        dst = dst.removeprefix("refs/heads/")
        if dst in ("", "HEAD", "@"):
            implicit = True
        else:
            explicit.append(dst)
    return explicit, implicit, all_refs


def _segment_actions(tokens: list[str], default_branches: tuple[str, ...] = DEFAULT_BRANCHES) -> tuple[set[str], bool, bool]:
    """(actions, push_implicit, uncertain_repo) for one segment."""
    if not tokens:
        return set(), False, False
    verb = tokens[0].rsplit("/", 1)[-1]
    if verb == "git":
        sub, args = _git_subcommand(tokens)
        redirected = any(t in _REPO_REDIRECTING_GIT_OPTS or t.startswith("--git-dir=") or t.startswith("--work-tree=")
                         for t in tokens[1:tokens.index(sub) if sub in tokens else len(tokens)])
        if sub == "commit":
            return {COMMIT}, False, redirected
        if sub == "push":
            actions = {PUSH, DELETE_REMOTE_BRANCH} if _is_delete_push(args) else {PUSH}
            explicit, implicit, all_refs = _push_destinations(args)
            if all_refs or any(dst in default_branches for dst in explicit):
                actions.add(PUSH_DEFAULT_BRANCH)
            return actions, implicit, redirected
        return set(), False, False
    if verb == "gh":
        rest = [t for t in tokens[1:] if not t.startswith("-")]
        if rest[:2] == ["pr", "create"]:
            return {OPEN_PR}, False, False
        if rest[:2] == ["pr", "merge"]:
            return {MERGE}, False, False
        if rest[:1] == ["api"]:
            joined = " ".join(tokens)
            if re.search(r"(?:-X|--method)[ =]DELETE\b", joined, re.IGNORECASE):
                return {DELETE_REMOTE_BRANCH}, False, False
    return set(), False, False


_REDIRECT_OUT = re.compile(r"^\d*>>?(?!&)(.*)$")


def _writes_via_redirect(tokens: list[str]) -> bool:
    """True when a token redirects output to something other than /dev/null (`> f`, `>>f`, `2> f`)."""
    for i, tok in enumerate(tokens):
        m = _REDIRECT_OUT.match(tok)
        if m:
            target = m.group(1) or (tokens[i + 1] if i + 1 < len(tokens) else "")
            if target != "/dev/null":
                return True
    return False


def _is_read_only(tokens: list[str]) -> bool:
    if not tokens:
        return True
    if _writes_via_redirect(tokens):
        return False
    verb = tokens[0].rsplit("/", 1)[-1]
    if verb in _READ_ONLY_VERBS:
        return True
    if verb == "git":
        sub, _ = _git_subcommand(tokens)
        return sub in _READ_ONLY_GIT
    return False


_UNRESOLVABLE_CD = re.compile(r"[$`*?\[]|^-$|^~[^/]")


def _cd_target(tokens: list[str]) -> tuple[bool, str | None]:
    """(is_cd, literal target). A target is None when it cannot be resolved without running the shell: a variable,
    command substitution, glob, `cd -` or `~user`. A bare `cd` is the home directory."""
    while tokens and tokens[0] in ("(", "{"):  # `( cd x && ... )`
        tokens = tokens[1:]
    if not tokens:
        return False, None
    head = tokens[0].lstrip("(")
    if head not in ("cd", "pushd"):
        return False, None
    args = [t for t in tokens[1:] if t == "-" or not t.startswith("-")]
    if not args:
        return True, "~" if head == "cd" else None
    if len(args) != 1 or _UNRESOLVABLE_CD.search(args[0]):
        return True, None
    return True, args[0]


def _switches_branch(tokens: list[str]) -> bool:
    if not tokens or tokens[0].rsplit("/", 1)[-1] != "git":
        return False
    sub, _ = _git_subcommand(tokens)
    return sub in ("checkout", "switch")


def classify_command(command: str, default_branches: tuple[str, ...] = DEFAULT_BRANCHES) -> Classification:
    """Classify a Bash command, splitting compound commands and checking every segment.

    Data (heredoc bodies, quoted text) is removed first (`strip_text`), so a note that merely mentions "push" is not one."""
    command = strip_text(command)
    actions: set[str] = set()
    details: list[str] = []
    uncertain = False
    push_implicit = False
    switches_branch = False
    cd_chain: list[str] = []
    bad_cd = cd_after_action = False
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
        is_cd, cd_to = _cd_target(tokens)
        if is_cd:
            if {COMMIT, PUSH} & actions:
                cd_after_action = True
            elif cd_to is None:
                bad_cd = True
            else:
                cd_chain.append(cd_to)
            continue
        seg_actions, seg_implicit, seg_redirected = _segment_actions(tokens, default_branches)
        actions |= seg_actions
        push_implicit = push_implicit or seg_implicit
        switches_branch = switches_branch or _switches_branch(tokens)
        if seg_redirected and ({COMMIT, PUSH} & seg_actions):
            uncertain = True
            details.append("git -C/--git-dir/--work-tree: the branch of the repository acted on is not the call's cwd")
        if mentions_governed and not _is_read_only(tokens):
            seg = segment
            if AUTHORITY_FILE in seg:
                actions.add(AUTHORITY_FILE_EDIT)
                details.append(f"non-read-only command touching {AUTHORITY_FILE}")
            if any(f in seg for f in GOVERNING_FILES):
                actions.add(GOVERNING_FILE_EDIT)
                details.append("non-read-only command touching a governing file")

    if {COMMIT, PUSH} & actions and (bad_cd or cd_after_action):
        uncertain = True
        details.append("a cd/pushd that cannot be resolved, or that follows the commit or push: the branch acted on is not known")
    if switches_branch and ({COMMIT, PUSH} & actions):
        uncertain = True
        details.append("a branch switch in the same command: the branch committed or pushed is not the cwd's current one")
    if DELETE_REMOTE_BRANCH in actions:
        details.append("remote branch deletion")
    return Classification(frozenset(actions), uncertain, "; ".join(dict.fromkeys(details)), push_implicit, tuple(cd_chain))
