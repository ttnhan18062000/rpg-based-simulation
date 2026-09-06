"""Architecture guard: IdentityComponent.faction may only be written via
IdentityUpdate.faction_set, threaded through the authoritative apply-path
(patches.py:209/apply.py:321). TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE gave this field
its first-ever real, live producer (PartyLifecycleService.check_defection()) -- this guard
prevents a second, bypassing write path from ever being introduced.

Scan strategy (mirrors tests/architecture/test_social_write_paths.py's exact precedent, adapted
after implementation-time verification found the field name "faction" -- unlike
"public_reputation"/"regional_reputation" -- is far too common a bare word/kwarg across src/ for
a plain `\\bfaction\\s*=` scan: it hits equality comparisons (`==`), local read-only variables
named `faction`, f-string labels, and dozens of legitimate `V2EntityBuilder(...).identity(
faction=...)` construction-time calls scattered across world-generation/assembly, none of which
are a bypass of the frozen IdentityComponent dataclass):
  - `faction_set\\s*=` catches a keyword-argument construction of IdentityUpdate(faction_set=...)
    anywhere outside the allowlist.
  - `replace\\([^)]*?faction\\s*=(?!=)` catches the actual realistic bypass shape:
    `dataclasses.replace(<identity-component-expr>, faction=X, ...)`. IdentityComponent is a
    frozen dataclass (src/core/state.py:576), so a literal `identity.faction = X` attribute
    assignment can never be written against it at all -- scanning for that pattern would give
    false confidence. This is scoped to `replace(...faction=...)` specifically (not bare
    `faction=` anywhere) because `.identity(faction=...)` is a differently-named builder DSL
    method call, not a `dataclasses.replace()` invocation -- confirmed via direct read that no
    such call exists anywhere in src/ today outside patches.py's own authoritative writer.
  - ALLOWED_FILES may contain them (the typed field declaration + merge(), the sole authoritative
    consumer, initial-construction seeding, and this ticket's new trigger).
  - Any other file containing either pattern is a second write path and fails the test.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import FrozenSet

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")

_FACTION_SET_PATTERN = re.compile(r'faction_set\s*=')
# Correction, found during an external pre-merge review (2026-09-06): the original
# `replace\([^)]*?faction\s*=(?!=)` cannot match across a single level of nested parens (e.g.
# `dataclasses.replace(entity.identity, role=get_default_role(), faction=Faction.NEUTRAL)` --
# `get_default_role()`'s own closing paren terminates `[^)]*?` before `faction=` is ever reached,
# silently evading the guard). Widened to tolerate one level of nested balanced parens via
# `(?:[^()]|\([^()]*\))*?`. This is not a full AST-based scan (unlike
# test_phase18_import_boundaries.py's own precedent) and would still miss two or more levels of
# nesting -- not a live risk today (the `faction_set=` pattern above independently covers the one
# realistic bypass shape that exists anywhere in src/ currently), but disclosed here rather than
# silently left as an unstated limitation.
_IDENTITY_REPLACE_FACTION_BYPASS_PATTERN = re.compile(
    r'replace\((?:[^()]|\([^()]*\))*?faction\s*=(?!=)', re.DOTALL
)

# Files permitted to contain `faction_set=`:
#   - updates.py: IdentityUpdate's field declaration + merge()/is_noop() plumbing
#   - patches.py: IdentityPatch.apply(), the sole authoritative consumer
#   - builder.py: V2EntityBuilder's initial-construction seeding (pre-tick, not a live mutation)
#   - party_lifecycle.py: this ticket's new trigger, check_defection()
FACTION_SET_ALLOWED_FILES: FrozenSet[str] = frozenset({
    "src/core/updates.py",
    "src/engine/patches.py",
    "src/core/builder.py",
    "src/systems/social_systems/party_lifecycle.py",
})

# Files permitted to contain `replace(...faction=...)`:
#   - patches.py: IdentityPatch.apply()'s own authoritative `replace(new_id, ..., faction=fac,
#     ...)` construction (patches.py:238-245) -- the sole authoritative writer.
IDENTITY_REPLACE_BYPASS_ALLOWED_FILES: FrozenSet[str] = frozenset({
    "src/engine/patches.py",
})


def _iter_src_py_files():
    return sorted(_SRC_ROOT.rglob("*.py"))


def test_faction_set_write_restricted_to_authoritative_writer():
    violations = []

    for path in _iter_src_py_files():
        rel_path = path.as_posix()
        if rel_path in FACTION_SET_ALLOWED_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        if _FACTION_SET_PATTERN.search(text):
            violations.append(rel_path)

    assert not violations, (
        "Found direct faction_set= write(s) outside the authoritative apply-path "
        "(and its allowlisted construction-time/trigger exceptions):\n"
        + "\n".join(f"  {path}" for path in violations)
    )


def test_identity_replace_faction_bypass_restricted_to_allowlist():
    violations = []

    for path in _iter_src_py_files():
        rel_path = path.as_posix()
        if rel_path in IDENTITY_REPLACE_BYPASS_ALLOWED_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        if _IDENTITY_REPLACE_FACTION_BYPASS_PATTERN.search(text):
            violations.append(rel_path)

    assert not violations, (
        "Found a dataclasses.replace(..., faction=...) bypass outside the authoritative "
        "IdentityPatch.apply() writer:\n"
        + "\n".join(f"  {path}" for path in violations)
    )


def test_party_lifecycle_py_is_the_defection_trigger():
    text = Path("src/systems/social_systems/party_lifecycle.py").read_text(encoding="utf-8")
    assert "faction_set=" in text


def test_apply_py_is_not_added_to_the_allowlist():
    """apply.py:321 only reads `u.identity.faction_set is not None` (a comparison) to
    invalidate the hostile/dead cache -- it never assigns faction_set, so it must not appear
    in either allowlist. This regex confirms the read site does not match the write pattern,
    per plan.md's explicit scope guard against defensively allowlisting it."""
    text = Path("src/engine/apply.py").read_text(encoding="utf-8")
    assert not _FACTION_SET_PATTERN.search(text)
    assert "src/engine/apply.py" not in FACTION_SET_ALLOWED_FILES
    assert "src/engine/apply.py" not in IDENTITY_REPLACE_BYPASS_ALLOWED_FILES
