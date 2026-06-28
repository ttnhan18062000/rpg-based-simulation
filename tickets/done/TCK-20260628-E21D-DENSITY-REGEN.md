---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260628-E21D-DENSITY-REGEN
phase: done
date: 2026-06-28
tags: [resource, ecology, density, regen, world-dynamics, p3]
---

# TCK-20260628-E21D-DENSITY-REGEN

## Title
Density-dependent resource regeneration (E21D)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Resource nodes in highly populated regions should regenerate slower, creating scarcity
pressure that drives entity migration and territorial competition. Implement a linear
density modifier (1.0 at 0 entities → 0.25 at ≥16 entities) applied to each node's
regen_rate_per_tick each ecology cycle.

## Scope
1. `src/world/ecology.py` — DENSITY_CAP=16 and DENSITY_FLOOR=0.25 class constants;
   `_region_entity_counts(state)` static method (O(N) entity scan, once per cycle);
   `_density_modifier(entity_count)` pure static method (linear interpolation);
   `process_ecology()` updated to build region counts and apply density_mod per node.
2. `docs/parity_ledger/town_resource.yaml` — new TOWN-187 entry.
3. Tests — 8 new E21D tests in `tests/unit/world/test_resource_ecology.py`.

## Out of Scope
- Cross-region pressure propagation (E21E — next child ticket).
- Density-based entity spawning suppression.
- Distinguishing entity kinds (all alive entities count equally).

## Acceptance Criteria
- [x] `_density_modifier(0)` == 1.0 (empty region — full regen).
- [x] `_density_modifier(16)` == 0.25 (at cap — floor regen).
- [x] `_density_modifier(8)` == 0.625 (half cap — linear midpoint).
- [x] `_density_modifier(32)` == 0.25 (above cap — clamped to floor).
- [x] Node in 16-entity region regens at 1/4 of base rate (4 → 1).
- [x] Node in empty region regens at full base rate (4 → 4).
- [x] effective_regen is always ≥ 1 even at max density.
- [x] Parity ledger TOWN-187 added.
- [x] All 25 ecology tests pass.

## Related Tickets
- Parent: TCK-20260628-E-RESOURCE-ECOLOGY
- Depends on: TCK-20260628-E21C-COMPILER-REGEN (DONE)
- Next: E21E-CROSS-REGION-PRESSURE

## Related Docs
- `docs/mechanics/03_economic_laws.md` (resource regeneration)
- `docs/parity_ledger/town_resource.yaml` (TOWN-187 added)

## Related Code Areas
- `src/world/ecology.py` (ResourceEcologyService)
- `src/engine/legality.py` (LegalityServiceV2.get_region_for_position)
- `tests/unit/world/test_resource_ecology.py` (Group E — 8 new tests)

## Assumptions / Open Questions
- All alive+active entities count equally regardless of type/faction.
- Dead entities (combat.alive=False) or inactive entities (lifecycle.active=False) excluded.
- Entity count is measured at ecology tick time (snapshot), not averaged over interval.

## Implementation Notes
- `_region_entity_counts` reuses `LegalityServiceV2.get_region_for_position()` — same method
  used in ecology for node region lookup. No new spatial infrastructure needed.
- Existing tests with `regions={}` are unaffected: `get_region_for_position` returns None
  when no regions exist, falling back to `entity_count=0` → `density_mod=1.0`.
- `max(1, ...)` floor on effective_regen prevents nodes from becoming permanently static
  in saturated regions — a deliberately conservative design.

## Test Summary
- 4 pure unit tests for `_density_modifier()` (no state, no side effects).
- 4 integration tests exercising density path through `process_ecology()` with real RegionState.
- All 25 ecology tests pass (0 regressions).

## Files Changed
- `src/world/ecology.py` (DENSITY_CAP, DENSITY_FLOOR, _region_entity_counts, _density_modifier,
  process_ecology density path)
- `docs/parity_ledger/town_resource.yaml` (TOWN-187 added)
- `tests/unit/world/test_resource_ecology.py` (8 new E21D tests, RegionState import)

## Completion Summary
Density-dependent regen implemented in ResourceEcologyService. Crowded regions (≥16 entities)
regen at 25% of base rate; empty regions regen at 100%. Linear interpolation for intermediate
counts. Effective regen floored at 1. All 25 ecology tests pass; TOWN-187 added to parity ledger.
