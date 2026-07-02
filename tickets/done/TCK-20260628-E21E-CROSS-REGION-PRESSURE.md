---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260628-E21E-CROSS-REGION-PRESSURE
phase: done
date: 2026-06-28
tags: [resource, ecology, pressure, cross-region, world-dynamics, p3]
---

# TCK-20260628-E21E-CROSS-REGION-PRESSURE

## Title
Cross-region scarcity pressure propagation (E21E)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Resource scarcity in one region should bleed pressure to adjacent regions, creating
a gradient that drives entity migration and territorial competition. Before E21E,
`RegionalPressureModel` evaluated each region's resource pressure independently
from events in that region alone — neighbouring regions with depleted nodes had no
observable effect on each other.

## Scope
1. `src/domains/world_emergence/models.py` — `RegionalPressureModel`:
   - `ADJACENCY_GAP = 50.0` and `PROPAGATION_FACTOR = 0.30` class constants
   - `_are_adjacent(r1, r2)` static method (bounding-box proximity test)
   - `propagate_cross_region(pressures, state)` static method
2. `src/domains/world_emergence/phase.py` — step 2b: call `propagate_cross_region`
   after `RegionalPressureModel.evaluate()`
3. `docs/parity_ledger/world_dynamics.yaml` — WORLD-104 added
4. Tests: 10 new E21E tests in `test_phase8_regional_pressure_model.py`

## Out of Scope
- Propagating danger or camp pressure cross-region (resource scarcity only)
- Dynamic adjacency graph (recomputed each call from current bounds)
- Pressure decay over multiple hops (single-hop only)

## Acceptance Criteria
- [x] Adjacent regions (bounding boxes within 50 units) share 30% of resource pressure
- [x] Bidirectional: both A→B and B→A applied simultaneously
- [x] Distant regions (>50 units apart) receive no propagated pressure
- [x] Region with no native pressure can receive propagated pressure from neighbours
- [x] Propagated intensity capped at 1.0
- [x] Danger/camp pressures unchanged by propagation
- [x] WORLD-104 added to parity ledger
- [x] All 240 world + world_emergence unit tests pass

## Related Tickets
- Parent: TCK-20260628-E-RESOURCE-ECOLOGY
- Depends on: E21C-COMPILER-REGEN, E21D-DENSITY-REGEN

## Related Docs
- `docs/parity_ledger/world_dynamics.yaml` (WORLD-104 added)
- `docs/mechanics/03_economic_laws.md` (resource pressure model)

## Related Code Areas
- `src/domains/world_emergence/models.py` (RegionalPressureModel.propagate_cross_region)
- `src/domains/world_emergence/phase.py` (step 2b wiring)
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`

## Implementation Notes
- `_are_adjacent` uses Chebyshev-style separating-axis test on bounding boxes:
  `hdist = max(0, max(x1min,x2min) - min(x1max,x2max))` and same for vertical.
  Both ≤ ADJACENCY_GAP → adjacent.
- Propagation is computed in a single pass (not iterative), so pressure can only
  spread one hop per ecology event window. This is intentional: prevents runaway
  cascades while still creating a meaningful gradient signal.
- Confidence for entries with spread mixed in: `min(orig.confidence, 0.75)`.
  For pure-propagation entries: 0.65 (lower certainty — indirect signal).

## Test Summary
- 4 tests for `_are_adjacent` (overlapping, touching, within-gap, beyond-gap)
- 6 tests for `propagate_cross_region` (no effect single-region, adjacent spread,
  bidirectionality, distant no spread, cap at 1.0, non-resource unchanged)
- All 240 world + world_emergence unit tests pass (0 regressions)

## Files Changed
- `src/domains/world_emergence/models.py` (ADJACENCY_GAP, PROPAGATION_FACTOR,
  _are_adjacent, propagate_cross_region, List import added)
- `src/domains/world_emergence/phase.py` (step 2b propagate_cross_region call)
- `docs/parity_ledger/world_dynamics.yaml` (WORLD-104 added)
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`
  (10 new E21E tests, RegionalPressure import added)

## Completion Summary
Cross-region scarcity propagation implemented in `RegionalPressureModel`. Adjacent
regions (within 50 units) share 30% of their resource pressure bidirectionally,
creating scarcity gradients that drive entity migration pressure. All 240 tests pass.
WORLD-104 added to parity ledger.
