---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION
artifact_type: test_plan
tags: [observability, engine, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION

## Regression Surface

- `tests/unit/observability/` (full directory), `tests/unit/kernel/`, `tests/integration/kernel/`.

## New Tests Required

`tests/unit/observability/test_event_shapers_deferred_instrumentation.py` (new, 14 tests):
registry membership (1), resource-node events (4), `faction_extinct` (5, including the
faction-reassignment case and the already-extinct no-op), `conservation_law_verified` cross-shaper
aggregation (4, via `run_shadow_shapers()` directly rather than the shaper class alone).

## Scoped Pytest Commands

```
pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q
```

## Anti-Drift Test Guards

- No autouse reset fixture needed — `DeferredInstrumentationShaper` has no per-run state.
- `conservation_law_verified` tests call `run_shadow_shapers()` directly (not the shaper class in
  isolation), since the aggregation logic lives at that level, reading Phase 1's combined output.

## Results (this session)

- `pytest tests/unit/observability/test_event_shapers_deferred_instrumentation.py -q`: 14 passed.
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  1045 passed, 6 skipped, 3 deselected (was 1031/6/3 after Child 5 — +14 matches exactly).
- Real kernel runs across `dungeon_crawl` (500t), `urban_political` (500t), `sandbox_world`
  (2000t): zero real hits for all 5 event types in this ticket's scope — cross-checked against
  Phase 1's own already-validated `resource_harvested`/`item_crafted`/`shop_transaction`, which
  also showed zero in these identical runs, confirming an environmental characteristic (sparse
  economic activity without additional scenario setup this investigation didn't attempt), not a
  shaper defect. `SHADOW` mode confirmed to run a full 500-tick kernel cleanly with no exceptions.
