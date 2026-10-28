"""Compose a session role card: function template + domain overlay + generated role and authority lines.

Read-only. The injected text of a template is its `## Card` section; everything else in the file is
rationale and is never injected. Ownership, routes, handover and authority are generated from the
manifest and the authority file, so no template restates them (define once).

Budget (plan section 5, step 3): about 456 tokens (lowered from 460 to 456 by TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT, owner confirms on the PR: worst card 446 after the fold + 10; raised from 440 to 460 by the owner via agent-working-planner-u24, 2026-10-22, TCK-20261022-APPROVALS-NOTIFY-BOTH-LEADS-BEFORE-ACTING; earlier: 415 to 440 by the owner via lead-planner, 2026-10-21, TCK-20261021-SESSION-ROLES-OWN-OBSERVABILITY-DOCS-AND-UNOWNED-ROOTS; precedent 400->415 on 2026-10-20, TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS). No tokenizer is installed in this repo, so the
measure is a deliberately conservative estimate, `ceil(len(text) / 3.5)`: path-heavy text tokenizes
at roughly 3 to 4 characters per token, so this over-counts prose and is about right for globs.
"""

from __future__ import annotations

import math
import os
import re
from pathlib import Path

from tools.sessions.roster import REPO_ROOT, Authority, Role, Roster, handover_rel

CARD_BUDGET_TOKENS = 456
CHARS_PER_TOKEN = 3.5
TEMPLATE_DIR = Path("docs/guidelines/session_roles")

_CARD_SECTION = re.compile(r"^## Card\s*\n(.*?)(?=^## |\Z)", re.DOTALL | re.MULTILINE)


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def _card_section(path: Path) -> str:
    match = _CARD_SECTION.search(path.read_text(encoding="utf-8"))
    if not match or not match.group(1).strip():
        raise ValueError(f"{path}: no `## Card` section")
    return match.group(1).strip()


_DIR_GLOB = re.compile(r"^(?P<parent>.+)/(?P<leaf>[^/*]+)/\*\*$")
_FIRST_SEGMENT_GLOB = re.compile(r"^(?P<parent>[^/*]+)/(?P<leaf>[^*]+?)/\*\*$")


_PLAIN_FILE = re.compile(r"^(?P<dir>(?:[^/*{},]+/)*)(?P<stem>[^/*{},]+)\.(?P<ext>[A-Za-z0-9]+)$")


def _merge_sibling_files(items: list[str]) -> list[str]:
    """Adjacent plain files in one directory with one extension and a shared stem prefix ending in `_` or `-` become
    one brace entry: `tools/graphify_link.py, tools/graphify_prune.py` -> `tools/graphify_{link,prune}.py`."""
    out: list[str] = []
    i = 0
    while i < len(items):
        m = _PLAIN_FILE.match(items[i])
        run = [m] if m else []
        j = i + 1
        while m and j < len(items):
            n = _PLAIN_FILE.match(items[j])
            if not n or (n.group("dir"), n.group("ext")) != (m.group("dir"), m.group("ext")):
                break
            run.append(n)
            j += 1
        if len(run) > 1:
            stems = [r.group("stem") for r in run]
            prefix = os.path.commonprefix(stems)
            cut = max(prefix.rfind("_"), prefix.rfind("-")) + 1
            if cut >= 3:
                leaves = ",".join(s[cut:] for s in stems)
                out.append(f"{m.group('dir')}{prefix[:cut]}{{{leaves}}}.{m.group('ext')}")
                i = j
                continue
        out.append(items[i])
        i += 1
    return out


def _fold_same_dir_files(items: list[str]) -> list[str]:
    """Adjacent file globs in one plain directory become one brace entry when that is shorter:
    `tools/graphify_{link,prune}.py, tools/search_*.py` -> `tools/{graphify_{link,prune}.py,search_*.py}`."""
    def split(item: str) -> tuple[str, str] | None:
        head, sep, leaf = item.rpartition("/")
        if not sep or not leaf or leaf.endswith("**") or leaf.endswith(" files)") or re.search(r"[*{},]", head):
            return None
        return head, leaf

    out: list[str] = []
    i = 0
    while i < len(items):
        first = split(items[i])
        j = i + 1
        while first and j < len(items) and (nxt := split(items[j])) and nxt[0] == first[0]:
            j += 1
        if first and j - i > 1:
            folded = f"{first[0]}/{{{','.join(split(it)[1] for it in items[i:j])}}}"
            if len(folded) < len(", ".join(items[i:j])):
                out.append(folded)
                i = j
                continue
        out.append(items[i])
        i += 1
    return out


def _group_globs(globs: list[str] | tuple[str, ...], pattern: re.Pattern[str]) -> str:
    return ", ".join(_group_glob_items(globs, pattern))


def _group_glob_items(globs: list[str] | tuple[str, ...], pattern: re.Pattern[str]) -> list[str]:
    groups: dict[str, list[str]] = {}
    order: list[str] = []
    for g in globs:
        m = pattern.match(g)
        key = m.group("parent") if m else g
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(m.group("leaf") if m else "")
    out = []
    for key in order:
        leaves = [leaf for leaf in groups[key] if leaf]
        if not leaves:
            out.append(key)
        elif len(leaves) == 1:
            out.append(f"{key}/{leaves[0]}/**")
        else:
            out.append(f"{key}/{{{','.join(leaves)}}}/**")
    return out


COUNT_NOTE = "N files: a count; exact list via `route`"
_COUNT_ITEM = re.compile(r"^.+/ \(\d+ files\)$")


def _owned_whole(directory: str, globs: list[str] | tuple[str, ...]) -> bool:
    """True when some glob owns `directory` as a whole (`dir/**` or an ancestor's `**`)."""
    return any(g.endswith("/**") and (directory == g[:-3] or directory.startswith(g[:-3] + "/")) for g in globs)


def _count_scattered_files(globs: list[str] | tuple[str, ...]) -> list[str]:
    """Two or more plain files in a directory the role does not own as a whole become one `dir/ (N files)` entry, at
    the first member's place, when that is shorter than their brace form. A file alone in its directory, files in an
    owned directory, and a group whose brace form is already shorter stay as they are."""
    plain: dict[str, list[str]] = {}
    for g in globs:
        m = _PLAIN_FILE.match(g)
        if m and m.group("dir"):
            plain.setdefault(m.group("dir").rstrip("/"), []).append(g)
    counted: dict[str, str] = {}
    for directory, files in plain.items():
        if len(files) < 2 or _owned_whole(directory, globs):
            continue
        shortest = min(
            len(", ".join(_fold_same_dir_files(_merge_sibling_files(files)))),
            len(f"{directory}/{{{','.join(f[len(directory) + 1:] for f in files)}}}"),
        )
        label = f"{directory}/ ({len(files)} files)"
        if len(label) < shortest:
            counted[directory] = label
    out: list[str] = []
    for g in globs:
        m = _PLAIN_FILE.match(g)
        directory = m.group("dir").rstrip("/") if m else ""
        if directory not in counted:
            out.append(g)
        elif counted[directory] not in out:
            out.append(counted[directory])
    return out


def has_count_entry(text: str) -> bool:
    return any(_COUNT_ITEM.match(part.strip()) for part in re.split(r",\s+(?![^{}]*\})", text))


def _compact_globs(globs: list[str] | tuple[str, ...], count_scattered: bool = False) -> str:
    """`docs/a/**, docs/b/**` -> `docs/{a,b}/**`: a shared parent is named once.

    Two groupings are tried, by shared full parent and by shared first segment
    (`docs/{a,b/c}/**`); the shorter string wins, the full-parent one on a tie, so
    no card grows against the older grouping.
    """
    if count_scattered:
        globs = _count_scattered_files(globs)
    by_parent = ", ".join(_fold_same_dir_files(_merge_sibling_files(_group_glob_items(globs, _DIR_GLOB))))
    by_first = ", ".join(_fold_same_dir_files(_merge_sibling_files(_group_glob_items(globs, _FIRST_SEGMENT_GLOB))))
    return by_first if len(by_first) < len(by_parent) else by_parent


def _routes_text(role: Role) -> str:
    """Routes grouped by target role, so a target is named once."""
    by_target: dict[str, list[str]] = {}
    for glob, target in role.routes:
        by_target.setdefault(target, []).append(glob)
    if not by_target:
        return ""
    return "Route elsewhere: " + "; ".join(f"{_compact_globs(globs)} -> {t}" for t, globs in by_target.items()) + "."


def _role_line(role: Role, roster: Roster) -> str:
    seat = "" if role.seat_status == "staffed" else f" (unstaffed, held by {role.interim_holder})"
    owns = _compact_globs(role.owns)
    counted = _compact_globs(role.owns, count_scattered=True)
    if has_count_entry(counted) and len(counted) + len(COUNT_NOTE) + 4 < len(owns):  # the note must pay for itself
        owns = f"{counted} ({COUNT_NOTE})"
    parts = [
        f"You are `{role.role}`{seat}. Owns: {owns}.",
        _routes_text(role),
        f"Dispatch from: {', '.join(role.accepts_dispatch_from)}." if role.accepts_dispatch_from else "",
        (f"Launches from the main checkout, no lease; `{role.handover}`" if role.launch == "main-checkout"
         else f"Worktree {role.worktree}; main-checkout `{role.handover}`") + (
            f" (instance N reads `{handover_rel(role, role.role + '-N')}`)." if role.max_sessions > 1 else "."),
    ]
    return " ".join(p for p in parts if p)


# An action the card need not print under "Needs the user" because "Never" already covers its parent: a role that
# never pushes does not need telling that a push to the default branch needs the user (TCK-20261006-GUARD-OWN-BRANCH-
# GIT-ALLOWED; keeps the designer and planner cards inside the budget without changing their text).
_IMPLIED_BY = {"push_default_branch": "push"}


def _authority_line(role: Role, authority: Authority) -> str:
    base = authority.for_function(role.function)
    if base is None:
        raise ValueError(f"no authority default for function {role.function!r}")
    line = f"Never: {', '.join(base.forbidden)}. " if base.forbidden else ""
    needs_user = [a for a in base.needs_user if _IMPLIED_BY.get(a) not in base.forbidden]
    line += f"Needs the user: {', '.join(needs_user)}."
    grants = authority.grants_for(role.role)
    if grants:
        line += " Granted: " + "; ".join(f"{'/'.join(g.actions)} ({g.date})" for g in grants) + "."
    return line


def compose_card(role_id: str, roster: Roster, authority: Authority, root: Path = REPO_ROOT) -> str:
    role = roster.role(role_id)
    if role is None:
        raise KeyError(role_id)
    function = _card_section(root / TEMPLATE_DIR / "functions" / f"{role.function}.md")
    domain = _card_section(root / TEMPLATE_DIR / "domains" / f"{role.domain}.md")
    parts = [_role_line(role, roster), function, domain]
    if role.card_note:
        parts.append(role.card_note)
    parts.append(_authority_line(role, authority))
    return "\n\n".join(parts)
