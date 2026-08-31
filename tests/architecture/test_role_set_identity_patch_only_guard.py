"""
Architecture guard: role_set commits only through the authoritative IdentityPatch.apply path.

TCK-20260824-OCCUPATION-CHANGE-TRIGGER's ActionIntentAdapter branch
(src/engine/intent/action_intent.py) is the sole new producer of IdentityUpdate(role_set=...) in
this codebase. This guard statically confirms that stays true, and that no bespoke parallel
mutation path (a direct `replace(..., role=...)` on an IdentityComponent outside
IdentityPatch.apply) is introduced.

Scoped narrower than a literal "no direct IdentityComponent( construction outside these files"
scan: src/core/builder.py (default no-arg IdentityComponent() construction) and
src/core/state.py's EntityState.to_readonly() (CORE-PERF-010's manual-constructor perf
optimization, which copies `role=id_comp.role` -- the SAME already-committed value, never a new
one) both construct IdentityComponent(...) directly for reasons unrelated to role mutation. A scan
that flagged those would be a false-positive noise generator, not a real guard -- the two checks
below (IdentityUpdate(role_set=...) producers, and replace(..., role=...) mutation sites) are what
actually enforce the Durable State Rule for this field.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")

_ROLE_SET_PRODUCER_PATTERN = re.compile(r"IdentityUpdate\([^)]*\brole_set\s*=")
_ROLE_MUTATION_PATTERN = re.compile(r"replace\([^)]*\brole\s*=")

_ALLOWED_ROLE_SET_PRODUCERS = frozenset({"engine/intent/action_intent.py"})
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


def test_identity_update_role_set_has_no_producer_outside_action_intent():
    hits = _scan(_ROLE_SET_PRODUCER_PATTERN)
    unexpected = {k: v for k, v in hits.items() if k not in _ALLOWED_ROLE_SET_PRODUCERS}
    assert not unexpected, (
        f"IdentityUpdate(role_set=...) constructed outside the sole sanctioned producer: {unexpected}"
    )
    assert "engine/intent/action_intent.py" in hits


def test_identity_role_mutation_has_no_site_outside_identity_patch_apply():
    hits = _scan(_ROLE_MUTATION_PATTERN)
    unexpected = {k: v for k, v in hits.items() if k not in _ALLOWED_ROLE_MUTATORS}
    assert not unexpected, (
        f"replace(..., role=...) found outside IdentityPatch.apply: {unexpected}"
    )
    assert "engine/patches.py" in hits
