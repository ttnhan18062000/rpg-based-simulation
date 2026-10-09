---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261009-PURSUING-GUARDS-RUN-HUNDREDS-OF-TILES-OFF-THE-MAP-AND-STARVE
phase: open
date: 2026-10-09
tags: []
---

# TCK-20261009-PURSUING-GUARDS-RUN-HUNDREDS-OF-TILES-OFF-THE-MAP-AND-STARVE

## Title
Guards in INTERCEPT, PURSUE or REPOSITION end up at coordinates far outside the map (x about 900 / y about -840, y 1640-1920) and starve there, on main as on batch 2.

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Lane B's batch-2 trace (2026-10-09; urban_political, seeds 42-46, 5000 ticks): 9 of 16 batch-2 guard starvation victims, 3 of 8 on main and 4 of 8 with profiles off died at positions far off the map while in INTERCEPT/PURSUE/REPOSITION, 1200-1900 tiles from the nearest inn. An entity position outside the world bounds breaks the movement legality the Bible and engine contracts require (Bible 02; the authoritative movement pipeline). It is an integrity defect before it is a starvation one.

## Scope
- Find how a position leaves the map: the pursuit/intercept target projection, a reposition target without clamping, or a movement step not checked against bounds.
- Fix at the authoritative movement/legality path, so no update can commit an out-of-bounds position. Add a hard-law or invariant check if none covers it (src/observability HardLawMonitor).
- A regression test reproducing it from one traced seed.

## Out of Scope
- Hero leash starvation (its own ticket).
- The CONFLICT-04 movement layer itself, unless it's the source.

## Acceptance Criteria
- No entity position outside the world bounds in the 5 urban seeds over 5000 ticks, checked by an invariant.
- Parity ledger (combat_movement.yaml) and the Bible are updated if the legality text changes.

## Related Tickets
Batch 2 (EXCH-02 tickets; the trace is in its PR). M0 gate (designer memo rows 52-54: H6, R1). TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT (adjacent, not the same).

## Related Docs
docs/mechanics/04_strategic_cognition.md; docs/mechanics/02_combat_laws.md; docs/engine/authoritative_pipeline.md.

## Related Stored Artifacts
Lane B's trace probe: /tmp/claude-1000/scratch27/trace2.py and an2.py (to be copied into batch 2's stored artifacts probes).

## Related Code Areas
src/engine/movement.py, src/engine/tactical.py (_resolve_target_position, intercept/pursue), src/engine/legality.py, src/observability.

## Assumptions / Open Questions
- LIKELY MECHANISM (code trace of origin/main, 2026-10-09): `chase_ticks` is never incremented (only copied at src/engine/apply.py:720), so should_give_up_chase fires on distance only (> 1.5x leash_radius). Only monster spawns get a leash (generator.py:152/192/226/308); the default leash_radius is 0.0 (state.py:500), so a guard has NO give-up condition at all, and a pursuit can run unbounded. Check that first.
- Whether the out-of-bounds step is committed by apply.py (Phase B held: read only; a fix there waits for Phase B).
- Lane: P1, the next free lane.

## Implementation Notes
- Designer's fiction lens (2026-10-09): a pursuer gives up at the edge of what it knows or can reach. Beyond the bounds clamp (integrity), the chase should end at the limit of perception or reach (behaviour).

## Test Summary
tests/engine/test_world_extent_and_chase.py (7 tests): extent is the union of regions, no extent when no regions, OUT_OF_BOUNDS from verify_occupancy, LAW-POSITION-IN-WORLD, intercept aims at a pursuing target's position and still leads a walker, a held target is let go beyond perception. 577 existing tests around the touched APIs pass. Paired measurement (seeds 41-45, 1500 ticks, pinned): out-of-world ticks per run 504 -> 0 (urban_political), 174 -> 0 (frontier_living_world).

## Files Changed
src/core/enums.py, src/engine/spatial_query.py, src/engine/legality.py, src/engine/positioning.py, src/engine/tactical.py, src/observability/hard_law_monitor.py, tests/engine/test_world_extent_and_chase.py, docs/mechanics/02_combat_laws.md, docs/parity_ledger/combat_movement.yaml, docs/guidelines/intentional_divergences.md.

## Completion Summary
Open. Integrity and the behaviour fix are built and measured. The chase-duration limit is deferred to after Phase B (chase_ticks is never incremented; it needs apply.py).
