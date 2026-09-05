---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-HOME-EXILE-REFUGEE-THREADS
phase: done
date: 2026-09-05
tags: [strategy, world]
---

# TCK-20260905-HOME-EXILE-REFUGEE-THREADS

## Title
Home, Exile & Return + Named Refugee Threads (M6 ideas 59+65) — populate an existing field, not invent new state

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Idea 59 (Home, Exile & Return) and idea 65 (Named Refugee Threads) are the M6 epic's third and
final child (`TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`), consolidated into one ticket per the
epic doc's own Shared Implementation Opportunities finding (idea 65 folds into idea 59's ticket as
extra acceptance criteria, writing `home_region_id` at displacement time).

**The single largest correction found during this milestone's original investigation, confirmed
real, not assumed:** idea 59's central premise — "no per-entity place-attachment field exists" — was
flatly wrong. `StrategicComponent.home_region_id: Optional[str] = None`
(`src/core/strategic.py:414`) already exists, typed, with a live consumer already wired
(`RoutineService.evaluate_anchored_behavior()`, `src/systems/world_systems/routine.py:163`, called
from `src/systems/strategic_systems/intelligence.py:541,857`). This ticket is
populate-an-existing-field at the right moments (birth/settlement, displacement/exile), not
invent-new-state — materially cheaper than the epic doc's original scoping assumed.

## Scope
- Confirm and, if needed, wire `home_region_id`'s population at the moments the epic doc names:
  birth/settlement (an entity's home is set once, early) and displacement (idea 65 — a refugee's
  `home_region_id` is written or updated at the moment of forced displacement, distinct from their
  new, non-home current location).
- Confirm `RoutineService.evaluate_anchored_behavior()`'s existing "return home" concern correctly
  reflects a freshly-set or updated `home_region_id`, not just the birth-time value, once idea 65's
  displacement-time write lands.
- Add any missing observable event/telemetry for a displacement (exile/refugee) event, if none
  exists today (confirm during Investigate — not assumed either way here).
- Document the mechanism in a real, citable doc.

## Out of Scope
- Idea 39 (Affiliation's real change path) — `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`.
- Idea 56 (Drifting Loyalty) — `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`.
- Inventing any new per-entity place-attachment field — `home_region_id` already exists and is the
  correct target; this ticket populates and reads it correctly, it does not replace it.
- Any UI/API surface for home/exile/refugee status unless a future ticket asks for it.

## Acceptance Criteria
- [x] `home_region_id` is correctly populated at birth/settlement for every new entity that should
      have one (confirm the exact population rule during Investigate — not assumed here).
- [x] A real displacement/exile trigger writes or updates `home_region_id` per idea 65's "named
      refugee threads" requirement — confirmed via a test constructing a displacement scenario.
- [x] `RoutineService.evaluate_anchored_behavior()`'s existing "return home" concern is confirmed
      (via a test) to correctly react to a post-displacement `home_region_id`, not just the
      birth-time value.
- [x] The mechanism is documented in a real, citable doc.
- [x] Parity-ledger entries added/updated for the affected file(s), each with a real `test_path`.

## Related Tickets
- `TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY` (parent epic)
- `TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE` (idea 39, sibling child, no hard dependency)
- `TCK-20260905-DRIFTING-LOYALTY-SIGNAL` (idea 56, sibling child, no hard dependency)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/core/strategic.py` (`StrategicComponent.home_region_id`)
- `src/systems/world_systems/routine.py` (`RoutineService.evaluate_anchored_behavior()`)
- `src/systems/strategic_systems/intelligence.py`

## Assumptions / Open Questions
- The exact displacement/exile trigger condition (calamity-driven, faction-conflict-driven, or both)
  is not decided here — real design work for this ticket's own Investigate/Plan phases.
- Whether this ticket can land in parallel with idea 39/56 or should wait, given it shares no hard
  code dependency with either — left to the implementer's own judgment at pickup time; the epic's
  SEQUENCE.md does not hard-block it behind the other two.

## Implementation Notes
- `StrategicUpdate.home_region_id_set: Optional[str] = None` added (`src/core/updates.py`), the
  reverse of every other `_set` field on that class: `StrategicPatch.apply()`
  (`src/engine/patches.py`) resolves `home_region_id=new_strat.home_region_id if new_strat.home_region_id
  is not None else u_strat.home_region_id_set` — an already-durable value always wins over a
  proposed update, so a refugee's original home is never overwritten.
- Birth-time population (idea 59): `HumanoidReproductionService.process_reproduction()`
  (`src/world/reproduction_humanoid.py`) already resolves the spawn region via
  `SpatialQueryService.get_region_at()` for its own population-nudge; that same `region` is now
  also passed into `EntityGenerator.spawn_humanoid_offspring()`'s new `home_region_id` parameter
  (`src/systems/world_systems/generator.py`), applied via `.strategic(home_region_id=...)` at
  construction.
- **Real architecture-boundary violation found and fixed mid-Implement**: an earlier draft
  resolved the birth region *inside* `generator.py` via `from src.engine.legality import
  LegalityServiceV2`, which `tests/architecture/test_phase18_import_boundaries.py::
  test_systems_do_not_import_engine_outside_pinned_exceptions` correctly flagged (`src/systems/`
  may not import `src/engine/` outside 13 pinned exceptions). Per the Gate Integrity rule, the
  import was **not** pinned as an exception; the resolution was moved to the caller
  (`src/world/reproduction_humanoid.py`, which is under `src/world/` and has no such
  restriction, and already computed the same region for another purpose) instead.
- New `DisplacementService.compute_displacement()` (`src/world/displacement.py`, idea 65): pure
  function, reads `AuthoritativeState`, returns a `StateUpdate`. Relocates every living entity in
  a region at/above `DISPLACEMENT_THRESHOLD` (0.6) `calamity_intensity` to its
  lowest-`calamity_intensity` adjacent region (reusing `RegionalPressureModel._are_adjacent()`
  read-only), via `EntityUpdate.new_position`. Wired into `src/engine/world_dynamics.py`
  immediately after the existing "3.9 Creature Territory Lifecycle" block, merged only if
  `not is_noop()`.
- Confirmed end-to-end (new integration test in `test_displacement.py`) that
  `RoutineService.evaluate_anchored_behavior()` — the pre-existing "return home" consumer — reads
  a displacement-time `home_region_id_set` write through `ApplyPath.apply_partial()` correctly,
  and targets the entity's original home, not their post-displacement physical location.
- Confirmed no `StateFingerprinter`/`CanonicalStateHasher` coverage gap existed for
  `home_region_id` or `navigation.position` — both were already covered before this ticket
  (unlike the two sibling M6 tickets, which each found and fixed a real gap).

## Test Summary
- `tests/unit/world/test_displacement.py` (new, 9 tests): noop-when-no-threshold, relocation to
  safest neighbor, `home_region_id` set when unset, preserved when already set, dead entities
  excluded, no-safe-neighbor noop, determinism across repeated calls, world_updates untouched,
  and the new end-to-end `RoutineService` integration test.
- `tests/architecture/test_displacement_write_paths.py` (new, 2 tests): guards
  `DisplacementService` never directly mutates `strategic`/`navigation`, only constructs typed
  updates.
- `tests/unit/world/test_reproduction_humanoid_cadence.py` (+2 tests):
  `home_region_id` set from spawn position; `home_region_id` `None` when no region resolves.
- Full regression: `tests/unit/world/ tests/unit/engine/ tests/architecture/ tests/unit/core/
  tests/unit/strategic/ -m "not slow"` — 1159 passed, 1 skipped, 3 deselected, zero failures.
- `tests/architecture/test_phase18_import_boundaries.py::
  test_systems_do_not_import_engine_outside_pinned_exceptions` re-confirmed passing after the
  architecture fix.

## Files Changed
- `src/core/updates.py` — `StrategicUpdate.home_region_id_set` field + `is_noop()`/`merge()`.
- `src/engine/patches.py` — `StrategicPatch.apply()` reversed-precedence `home_region_id`
  resolution.
- `src/systems/world_systems/generator.py` — `spawn_humanoid_offspring()` new `home_region_id`
  parameter.
- `src/world/reproduction_humanoid.py` — passes resolved `region.id` into the new parameter.
- `src/world/displacement.py` (new) — `DisplacementService`.
- `src/engine/world_dynamics.py` — displacement wiring (3.9b).
- `tests/unit/world/test_displacement.py` (new), `tests/architecture/test_displacement_write_paths.py`
  (new), `tests/unit/world/test_reproduction_humanoid_cadence.py` (+2 tests).
- `docs/world/home_exile_refugee_contract.md` (new).
- `docs/plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md` — idea 59/65 status
  annotations, tracking-ticket line, Acceptance Signal.
- `docs/parity_ledger/world_dynamics.yaml` (`WORLD-DISPLACE-001`),
  `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-271`).

## Completion Summary
Both consolidated ideas (59: Home, Exile & Return; 65: Named Refugee Threads) landed as scoped —
populate-an-existing-field, not invent-new-state, exactly as the epic's own correction predicted.
A real architecture-boundary violation was found during Implement (systems importing engine) and
fixed by moving region resolution to the already-engine-importing caller rather than pinning a
new exception. This was the last of the M6 epic's 3 child tickets; `TCK-20260823-EPIC-RPG-M6-
POLITICAL-IDENTITY` is closed in the same batch.
