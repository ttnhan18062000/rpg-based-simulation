---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME
artifact_type: test_plan
tags: [content, observability]
---

# Test Plan — TCK-20260904-SPECIES-CROSSCUTTING-CONSUMERS-RENAME

## Files fixed
- `src/content/schema.py`, `data/content/social/factions.yaml`,
  `tests/unit/content/test_layered_catalog.py` (`common_races` → `common_species`)
- `src/observability/event_shapers.py`, `tests/unit/observability/test_event_shapers.py`
  (deferred output key `"race_id"` → `"species_id"`)
- `src/engine/cognition.py`, `tests/unit/content_semantics/test_semantics.py`
  (comment accuracy only)

## Result
- `tests/unit/observability/ tests/unit/content/ tests/unit/content_semantics/` (`-m "not slow"`)
  → **1324 passed, 1 skipped**.
- Full repo non-slow sweep: `tests/unit/ tests/integration/` (`-m "not slow"`) → **6008 passed, 9
  skipped, 84 deselected, 2 failed**. Both failures are the identical `tests/conftest.py:68`
  resource-time-limit `TimeoutError` diagnosed as environment-load noise in child 1/2's own
  test_plan.md (same two tests, same signature, unrelated to species/race identity logic) — no new
  regressions from this ticket's changes.
- Full repo-wide grep confirms zero remaining `race_id`/`RaceDefinition`/`common_races` references
  outside historical TCK-ID citations, the race-relations-subsystem's own scope (child 2, untouched
  here), and unrelated concurrency "race" terminology.
