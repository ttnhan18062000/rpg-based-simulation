---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-SCHEMA-MIGRATION
artifact_type: test_plan
tags: [content]
---

# Test Plan — TCK-20260902-PLACE-SCHEMA-MIGRATION

**Normal flow:** `PlaceState` constructs with minimal required fields, all optional fields default
correctly; all 7 `PlaceKind` values construct without error.

**Edge cases:** `RegionState` with zero Places (empty wilderness) vs. multiple Places; the
`prior_kind`/`transformed_tick` transformation trail on a transformed Place.

**Failure modes:** a hand-rolled fast-constructor (`ApplyPath._fast_replace_navigation`) missing a new
field raises `AttributeError` at runtime under the real tick-apply pipeline — caught only by running the
actual integration/worldbuilding smoke test, not unit tests alone. This is the single most
regression-prone path for any future field addition to `NavigationComponent`.

**Regression-prone paths:** full existing determinism/certification/worldbuilding suite, since this
touches `AuthoritativeState`, `NavigationComponent`, and `BuildingState` — all hot-path, widely-consumed
classes.

**Scope command (used):**
`pytest tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/ tests/unit/worldbuilding/ -m "not slow"`
— 699 passed, 2 skipped (pre-existing, unrelated), 0 failed.
Also: `pytest tests/certification/test_recorder_refactor.py tests/unit/worldbuilding/test_world_compiler.py tests/arena/ -m "not slow"`
— 76 passed.
`tests/integration/world/test_long_run_stability.py` excluded — `@pytest.mark.extra_slow`, explicitly
`skipif(CI==true)` for documented wall-clock non-determinism, unrelated to this change.
