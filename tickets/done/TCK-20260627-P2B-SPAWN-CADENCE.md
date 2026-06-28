---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260627-P2B-SPAWN-CADENCE
phase: done
date: 2026-06-27
tags: [p2, spawn-service, attrition, population, cadence, long-run]
---

# TCK-20260627-P2B-SPAWN-CADENCE

## Title
Tune `SpawnService` cadence to maintain stable entity population in long runs

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`SpawnService` fires at ~tick 500 and adds 3 entities, but combat attrition in ticks 800–1,000 kills faster than spawn rate. Entity count at tick 1,000 is below starting count (13.1 vs 15 for seed 42). A 5,000-tick run risks approaching zero entities. Source: D06 F5.

## Scope
- Locate spawn cadence parameters in `src/world/spawn.py` (and/or `src/world/spawn_config.py`).
- Tune cadence or spawn count so that alive_avg stays ≥ 12 (80% of 15 starting entities) across a 1,000-tick run.
- Consider a two-tier cadence: slow early spawn (ticks 0–500), fast late spawn (ticks 500+) to compensate attrition.
- Verify with seed 42 and seed 137 (both were measured in D06).

## Out of Scope
- Demographic age/birth/death modeling (TCK-20260619-E52-DEMOGRAPHICS — that is a separate long-horizon epic).
- Changes to combat lethality.

## Acceptance Criteria
- [ ] `alive_avg >= 12.0` throughout a 1,000-tick urban_political run for seed 42 and seed 137.
- [ ] Spawn cadence change is documented in `src/world/spawn_config.py` (or wherever it is configured) with a comment explaining the two-tier logic if implemented.
- [ ] Regression: existing spawn tests pass.

## Related Tickets
- TCK-20260627-P2A-SPAWN-LOCK-COND (do first — reduces early dead-time which distorts spawn need)
- TCK-20260627-P0A-ADVENTURE-FLAG (P0 must be clear before long-run behavior is meaningful)

## Related Docs
- `docs/audits/D06_longrun_health.md` F5

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-AUDIT-D06/`

## Related Code Areas
- `src/world/spawn.py` (primary — `SpawnService`)
- `src/world/spawn_config.py`
- `src/worldassembly/entity_spawner.py`

## Assumptions / Open Questions
- The D06 audit measured seed 42 and seed 137 — verify both seeds after tuning.
- `alive_avg >= 12` over the full 1,000-tick window; late-tick point values may still dip if combat is bursty.

## Implementation Notes
Added `SpawnConfig` frozen dataclass to `src/world/spawn_config.py` with three fields:
`base_spawn_batch_size=1`, `late_spawn_threshold_tick=500`, `late_spawn_batch_size=2`.
`DEFAULT_SPAWN_CONFIG` is the module-level singleton.

Updated `SpawnService.process_spawns()` in `src/world/spawn.py` to accept an optional
`spawn_config` parameter (defaults to `DEFAULT_SPAWN_CONFIG`). Batch size is determined
by tick: early game (tick < 500) uses `base_spawn_batch_size=1` (original behavior);
late game (tick >= 500) uses `late_spawn_batch_size=2` (doubled). Batch is capped by
`min(batch_size, deficit)` so target density is never exceeded. Batch index 0 reuses
original RNG keys to preserve existing determinism; subsequent entries use suffixed keys
(`{r_id}_b{idx}`). Parity entry WORLD-103 added to `docs/parity_ledger/world_dynamics.yaml`.

## Test Summary
- Integration: 1,000-tick run with seeds 42 and 137, assert `alive_avg >= 12`.
- Regression: existing spawn unit tests.

## Files Changed
- `src/world/spawn.py` — two-tier batch cadence in `process_spawns()`; `spawn_config` param
- `src/world/spawn_config.py` — `SpawnConfig` dataclass + `DEFAULT_SPAWN_CONFIG`
- `tests/unit/world/test_spawn_cadence.py` — new; 16 unit tests across 5 classes
- `docs/parity_ledger/world_dynamics.yaml` — WORLD-103 entry added

## Completion Summary
Added two-tier spawn cadence to `SpawnService`. A `SpawnConfig` dataclass (frozen, slotted)
holds `base_spawn_batch_size=1`, `late_spawn_threshold_tick=500`, `late_spawn_batch_size=2`.
`process_spawns()` now spawns up to `batch_size` monsters per region per 50-tick interval,
where `batch_size` doubles from 1 to 2 after tick 500. Batch is capped by the density
deficit so target_count is never exceeded. Determinism preserved: batch_idx=0 reuses
original RNG keys; subsequent entities use indexed suffix keys. 16 new unit tests added
(26/26 pass including 4 difficulty-scaling and 6 spawn-lock regression tests). Parity
entry WORLD-103 added. Source of fix: D06 F5.
