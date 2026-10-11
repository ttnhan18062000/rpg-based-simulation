"""Compose a session role card: function template + domain overlay + generated role and authority lines.

Read-only. The injected text of a template is its `## Card` section; everything else in the file is
rationale and is never injected. Ownership, routes, handover and authority are generated from the
manifest and the authority file, so no template restates them (define once).

Budget (plan section 5, step 3): about 400 tokens. No tokenizer is installed in this repo, so the
measure is a deliberately conservative estimate, `ceil(len(text) / 3.5)`: path-heavy text tokenizes
at roughly 3 to 4 characters per token, so this over-counts prose and is about right for globs.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from tools.sessions.roster import REPO_ROOT, Authority, Role, Roster, handover_rel

CARD_BUDGET_TOKENS = 400
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


def _group_globs(globs: list[str] | tuple[str, ...], pattern: re.Pattern[str]) -> str:
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
    return ", ".join(out)


def _compact_globs(globs: list[str] | tuple[str, ...]) -> str:
    """`docs/a/**, docs/b/**` -> `docs/{a,b}/**`: a shared parent is named once.

    Two groupings are tried, by shared full parent and by shared first segment
    (`docs/{a,b/c}/**`); the shorter string wins, the full-parent one on a tie, so
    no card grows against the older grouping.
    """
    by_parent = _group_globs(globs, _DIR_GLOB)
    by_first = _group_globs(globs, _FIRST_SEGMENT_GLOB)
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
    parts = [
        f"You are `{role.role}`{seat}. Owns: {_compact_globs(role.owns)}.",
        _routes_text(role),
        f"Dispatch from: {', '.join(role.accepts_dispatch_from)}." if role.accepts_dispatch_from else "",
        f"Worktree {role.worktree}; main-checkout `{role.handover}`" + (
            f" (instance N of `{role.role}` reads `{handover_rel(role, role.role + '-N')}`)." if role.max_sessions > 1 else "."),
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
    return "\n\n".join([_role_line(role, roster), function, domain, _authority_line(role, authority)])
