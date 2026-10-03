---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS
artifact_type: test_plan
tags: [observability, engine, simulation-quality]
---

# test_plan.md — TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS

## Regression Surface

- `tests/unit/observability/` (full directory), `tests/unit/kernel/`, `tests/integration/kernel/`.

## New Tests Required

`tests/unit/observability/test_event_shapers_world_dynamics.py` (new, 25 tests): registry
membership (1), demographic events (4, including the `demographic_mortality` combat-exclusion and
missing-prior-entity cases), boss/raid spawn + narrative_milestone (4), tick-modulo events (4),
`world_updates`-driven region events (6), `building_sabotaged` (2), `calamity_spawned` (2),
`world_events_add`-driven events (4).

## Scoped Pytest Commands

```
pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q
```

## Anti-Drift Test Guards

- No autouse reset fixture needed — `WorldDynamicsShaper` has no per-run state.

## Results (this session)

- `pytest tests/unit/observability/test_event_shapers_world_dynamics.py -q`: 25 passed.
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  1011 passed, 6 skipped, 3 deselected (was 986/6/3 after Child 3 — +25 matches exactly, no
  cross-shaper isolation issue this time).
- Real kernel runs across `dungeon_crawl`/`urban_political`/`hero_guild_routing` (500 ticks each):
  exact 1:1 parity between `event_extractor`/`event_shapers` for every event type that fired
  (`ecology_cycle_completed`, `region_trauma_delta`). `SHADOW` mode confirmed 0
  WorldDynamics-specific deliveries (after correcting an initial verification-script flaw that
  conflated Phase 1's own already-live shaper output with a Phase 2 leak — see investigation.md).
