---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION
artifact_type: test_plan
tags: [combat, faction, root-cause]
---

# Test Plan — TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION

Investigation only — no fix built, so no new test suite. What was actually checked:

- **Real call-site enumeration**: `grep -rn "get_engaged_hostiles" src/` confirmed exactly 2
  independent call sites (both in `src/engine/movement.py`) plus the internal wrapper
  relationship in `src/engine/legality.py` — no other real callers anywhere in `src/`.
- **Real call-volume measurement**: instrumented both `get_engaged_hostiles_at_pos` (the shared
  underlying primitive) and `get_engaged_hostiles` (the entity-own-position wrapper) separately,
  over real `Kernel.tick_once()` runs (`LocalSequentialExecutor`, `WorldCompiler.compile()` for
  corpus worlds, `build_metropolis_state()` for the metropolis control with its own spawn-collision
  limitation disclosed, not treated as clean), across 4 worlds. Sidestep-loop-only volume computed
  by subtraction (`at_pos calls - wrapper calls`), not assumed.
- **Existing test-fixture compatibility check**: traced `tests/unit/movement/
  test_movement_spatial_regression.py`'s escape-tag fixtures (`_build_evasive_retreat_pair`)
  through `EntityIdentityResolver.resolve()`'s real fallback path and `is_hostile_compat()`'s own
  real fallback branch by hand, to determine whether the existing test would still pass under
  catalog-aware semantics — not assumed, traced to a concrete conclusion.
- **Registry validation**: `tools/mechanism_registry/registry.py`'s `validate()` (via
  `python3 -m tools.mechanism_registry.mechanism_registry_completeness_check`) returns zero
  errors after adding the 3 `implemented_by` bindings.
- **Regression check on the 3 new bindings**: `pytest tests/unit/tools/test_mechanism_registry.py`
  (52/52 passed) and `pytest tests/unit/movement/` (57/57 passed, unrelated to the registry change
  but run for confidence since this investigation read that module closely).
