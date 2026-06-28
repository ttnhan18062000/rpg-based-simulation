---
status: done
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260628-E52E-SEASONAL-PROPAGATION
phase: done
date: 2026-06-28
tags: [world-evolution, calamity, propagation, seasonal, p3]
---

# TCK-20260628-E52E-SEASONAL-PROPAGATION

## Title
Seasonal calamity pressure propagation between adjacent regions

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement seasonal multi-region calamity pressure propagation. When a region has
`calamity_intensity >= 0.10`, a fraction of that intensity spreads to adjacent regions
every 500 ticks (one "season"). Wired into WorldDynamicsSystem as step 3.8.

## Scope
- `CalamityPressurePropagator.propagate_seasonal()` in `src/world/calamity.py`
- Wire into `src/engine/world_dynamics.py` as step 3.8 (runs every 500 ticks)
- Adjacency reuses `RegionalPressureModel._are_adjacent()`
- `SEASONAL_PROPAGATION_INTERVAL=500`, `PROPAGATION_FACTOR=0.15`, threshold=0.10
- Parity ledger entry in `docs/parity_ledger/world_dynamics.yaml`
- Tests

## Out of Scope
- Trauma propagation (separate path)
- Content authoring (calamity triggers in YAML)

## Acceptance Criteria
- [ ] `propagate_seasonal()` returns noop when tick % 500 != 0
- [ ] Adjacent region receives `calamity_intensity += source * 0.15`, capped at 1.0
- [ ] Non-adjacent region is unaffected
- [ ] Source region below threshold (< 0.10) does not propagate
- [ ] Wired in world_dynamics.py step 3.8; merged into update
- [ ] Tests pass

## Related Tickets
- Parent epic: TCK-20260628-E-WORLD-EVOLUTION
- Successor: TCK-20260628-E52F-TRAUMA-MOTIVATION

## Related Code Areas
- `src/world/calamity.py`
- `src/engine/world_dynamics.py`
- `src/domains/world_emergence/models.py` — `_are_adjacent` reuse

## Assumptions / Open Questions
- "Adjacent" uses same ADJACENCY_GAP=50 from E21E RegionalPressureModel._are_adjacent
- Intensity set via WorldUpdate.calamity_intensity_set; takes max of existing vs propagated

## Implementation Notes
- `CalamityPressurePropagator` added to `src/world/calamity.py` as a separate class from `CalamityService`.
- Per-neighbor update accumulates maximum across all sources (not sum) to prevent runaway amplification when multiple high-intensity regions feed the same neighbor.
- `state.tick == 0` special-cased separately from the modulo check to avoid tick-0 false positive.
- Wire: step 3.8 inside the `if should_run(state.tick, None, cadence.world_dynamics):` block; `merge()` only called when update is not noop.

## Test Summary
8 tests in `tests/unit/world/test_calamity_pressure_propagator.py`:
- noop at non-seasonal tick; noop at tick 0; noop when no region above threshold
- adjacent region receives spread; non-adjacent unaffected; capped at 1.0
- source not self-updated; propagation at second seasonal tick
221 world unit tests pass; no regressions.

## Files Changed
- `src/world/calamity.py` — CalamityPressurePropagator class added
- `src/engine/world_dynamics.py` — step 3.8 seasonal propagation wired
- `tests/unit/world/test_calamity_pressure_propagator.py` — 8 E52E tests (new file)
- `docs/parity_ledger/world_dynamics.yaml` — WORLD-105 added

## Completion Summary
Seasonal calamity_intensity propagation implemented: every 500 ticks, high-intensity regions spread 15% of their intensity to adjacent neighbors. Wired into WorldDynamicsSystem. 8 tests pass.

