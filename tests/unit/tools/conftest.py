"""Shared fixtures for tests/unit/tools/.

TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION: `registry.py::validate()`'s new
missing-system/orphan-system invariants (9/10) check every mechanism's own `systems: []` against
`registries/system_registry.jsonl`, the REAL, always-loaded registry — unlike `layers` and
`unaudited_depends_on_edges`, which are self-contained fields inside the `data` dict `validate()`
already receives. Every pre-existing test in this directory passes a minimal, self-contained
fixture that never declares `systems: []` at all, so without this fixture, invariant 10 (orphan
system) would fail every one of them: none of the 7 real registered systems has a member in a
2-3-mechanism synthetic fixture.

This autouse fixture patches the registry lookup to return an empty registry by default (zero
registered systems -> both invariants are vacuously satisfied for any fixture that doesn't
mention `systems` at all). Tests that specifically exercise invariants 9/10 override this default
explicitly via `monkeypatch.setattr` in their own test body, the same way they'd override any
other fixture-scoped dependency.
"""
from __future__ import annotations

import pytest

from tools.mechanism_registry import registry as _registry_module


@pytest.fixture(autouse=True)
def _empty_system_registry_by_default(monkeypatch):
    monkeypatch.setattr(_registry_module, "_load_system_registry", lambda *a, **kw: {})
