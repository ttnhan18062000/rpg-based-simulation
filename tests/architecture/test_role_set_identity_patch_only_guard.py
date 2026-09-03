"""
Architecture guard: role_set commits only through the authoritative IdentityPatch.apply path.

Two sanctioned producers of a role_set value exist in this codebase:
- TCK-20260824-OCCUPATION-CHANGE-TRIGGER's ActionIntentAdapter branch
  (src/engine/intent/action_intent.py), constructing a fresh `IdentityUpdate(role_set=...)`.
- TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE's lifecycle CHILD->ADULT archetype-choice branch
  (src/systems/lifecycle_systems/lifecycle.py), which instead refines an already-built
  `IdentityUpdate` via `replace(ent_upd.identity, role_set=...)` -- same typed field, same
  authoritative apply path (IdentityPatch.apply / EntityUpdate.apply), different call shape since
  it is composing onto an update that resolve_lifecycle() already produced for life_stage_set
  rather than constructing a bare IdentityUpdate from scratch.
This guard statically confirms role_set production stays confined to exactly these two sites, and
that no bespoke parallel mutation path (a direct `replace(..., role=...)` on an IdentityComponent
outside IdentityPatch.apply) is introduced.

Scoped narrower than a literal "no direct IdentityComponent( construction outside these files"
scan: src/core/builder.py (default no-arg IdentityComponent() construction) and
src/core/state.py's EntityState.to_readonly() (CORE-PERF-010's manual-constructor perf
optimization, which copies `role=id_comp.role` -- the SAME already-committed value, never a new
one) both construct IdentityComponent(...) directly for reasons unrelated to role mutation. A scan
that flagged those would be a false-positive noise generator, not a real guard -- the two checks
below (IdentityUpdate/.identity role_set=... producers, and replace(..., role=...) mutation sites)
are what actually enforce the Durable State Rule for this field.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")

_ROLE_SET_PRODUCER_PATTERN = re.compile(
    r"IdentityUpdate\([^)]*\brole_set\s*="
    r"|replace\([^)]*\.identity[^)]*\brole_set\s*="
)
_ROLE_MUTATION_PATTERN = re.compile(r"replace\([^)]*\brole\s*=")

_ALLOWED_ROLE_SET_PRODUCERS = frozenset({
    "engine/intent/action_intent.py",
    "systems/lifecycle_systems/lifecycle.py",
})
_ALLOWED_ROLE_MUTATORS = frozenset({"engine/patches.py"})


def _scan(pattern: re.Pattern) -> dict[str, list[int]]:
    hits: dict[str, list[int]] = {}
    for py_file in sorted(_SRC_ROOT.rglob("*.py")):
        if "__pycache__" in py_file.parts:
            continue
        rel = str(py_file.relative_to(_SRC_ROOT))
        text = py_file.read_text(encoding="utf-8")
        matches = [m.start() for m in pattern.finditer(text)]
        if matches:
            hits[rel] = matches
    return hits


def test_identity_update_role_set_has_no_producer_outside_sanctioned_sites():
    hits = _scan(_ROLE_SET_PRODUCER_PATTERN)
    unexpected = {k: v for k, v in hits.items() if k not in _ALLOWED_ROLE_SET_PRODUCERS}
    assert not unexpected, (
        f"role_set=... produced outside the sanctioned producers: {unexpected}"
    )
    assert "engine/intent/action_intent.py" in hits
    assert "systems/lifecycle_systems/lifecycle.py" in hits


def test_identity_role_mutation_has_no_site_outside_identity_patch_apply():
    hits = _scan(_ROLE_MUTATION_PATTERN)
    unexpected = {k: v for k, v in hits.items() if k not in _ALLOWED_ROLE_MUTATORS}
    assert not unexpected, (
        f"replace(..., role=...) found outside IdentityPatch.apply: {unexpected}"
    )
    assert "engine/patches.py" in hits
