"""
Architecture guards for TCK-20260905-HOME-EXILE-REFUGEE-THREADS (ideas 59+65,
"Home, Exile & Return" + "Named Refugee Threads" -- M6 Political Identity epic).

DisplacementService.compute_displacement() is a pure function: it must only ever
construct EntityUpdate/StrategicUpdate objects and never directly mutate a
StrategicComponent, NavigationComponent, or EntityState -- all durable writes go
through the authoritative apply-path (src/engine/patches.py).

Follows the same inspect.getsource()/source-text-scan technique as
tests/architecture/test_fidelity_write_paths.py and
tests/architecture/test_clan_reputation_write_paths.py.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

_DISPLACEMENT_MODULE = Path("src/world/displacement.py")

# dataclasses.replace(entity.strategic, ...) / dataclasses.replace(entity.navigation, ...) or
# object.__setattr__ on either component would bypass the authoritative apply-path.
_DIRECT_MUTATION_PATTERN = re.compile(
    r"\breplace\(\s*(?:\w+\.)?(strategic|navigation)\b|object\.__setattr__"
)


def test_displacement_service_never_directly_mutates_strategic_or_navigation():
    text = _DISPLACEMENT_MODULE.read_text(encoding="utf-8")
    matches = _DIRECT_MUTATION_PATTERN.findall(text)
    assert not matches, (
        "src/world/displacement.py must only construct EntityUpdate/StrategicUpdate "
        f"objects, never mutate strategic/navigation directly. Found: {matches}"
    )


def test_displacement_service_only_constructs_typed_updates():
    """DisplacementService.compute_displacement() must return its result via
    StateUpdate(entity_updates=...) with EntityUpdate/StrategicUpdate values -- never a
    raw dict assignment into an entity's own component fields."""
    text = _DISPLACEMENT_MODULE.read_text(encoding="utf-8")
    assert "EntityUpdate(" in text
    assert "StrategicUpdate(" in text
    assert "StateUpdate(" in text
    # No direct AuthoritativeState/EntityState field assignment anywhere in this module.
    assert not re.search(r"entity\.strategic\s*=", text)
    assert not re.search(r"entity\.navigation\s*=", text)
