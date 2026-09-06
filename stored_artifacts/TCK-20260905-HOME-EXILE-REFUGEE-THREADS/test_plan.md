---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-HOME-EXILE-REFUGEE-THREADS
artifact_type: test_plan
tags: [strategy, world]
---

# Test Plan — TCK-20260905-HOME-EXILE-REFUGEE-THREADS

## Regression Surface (existing tests that must pass)

- `tests/unit/world/test_boss.py` — confirms `home_region_id` boss-population path unaffected.
- `tests/unit/strategic/` (routine/anchored-behavior tests) — `evaluate_anchored_behavior()`
  unmodified behavior for existing callers.
- `tests/unit/world/test_calamity.py` — `CalamityService`/`CalamityPressurePropagator` unmodified
  behavior beyond the new read-only displacement consumer.
- `tests/unit/world/test_reproduction_humanoid_cadence.py`,
  `tests/unit/world/test_natural_creature_reproduction.py` — `spawn_humanoid_offspring()` signature
  extension stays backward-compatible (new kwarg optional, default preserves old behavior).
- `tests/unit/replay/` — `StateFingerprinter` coverage for existing fields unchanged.

## New Tests Required (per AC)

1. `test_home_region_id_populated_at_humanoid_birth_from_spawn_position` — a humanoid offspring
   spawned at a position resolving to a real region gets `strategic.home_region_id` set to that
   region's id.
2. `test_home_region_id_none_when_spawn_position_resolves_to_no_region` — parentless/edge-case spawn
   with no resolvable region leaves `home_region_id` as `None` (no crash).
3. `test_displacement_relocates_entity_when_region_calamity_intensity_crosses_threshold` — an entity
   in a region whose `calamity_intensity` crosses the threshold gets `navigation.position` updated to
   a lower-intensity neighboring region.
4. `test_displacement_sets_home_region_id_only_if_previously_unset` — a displaced entity with no
   prior `home_region_id` gets it set to their pre-displacement region; an entity with an
   already-set `home_region_id` (e.g. a boss) keeps their original value unchanged through
   displacement.
5. `test_displaced_entity_generates_return_home_concern_via_existing_consumer` — after displacement,
   `RoutineService.evaluate_anchored_behavior()` (unmodified) now emits `concern_return_home` for
   the refugee, proving the existing consumer becomes meaningful with zero changes to itself.
6. `test_displacement_writes_go_through_authoritative_apply_path` — architecture guard: no direct
   `EntityState`/`StrategicComponent`/`NavigationComponent` mutation outside `apply.py`.
7. `test_displacement_determinism_no_unsorted_iteration` — repeated calls with the same input state
   produce byte-identical `StateUpdate` output; guards against the unsorted-iteration bug class
   (`belief_institution/deriver.py`, PR #128).
8. `test_state_fingerprinter_covers_home_region_id` — `home_region_id` participates in
   `StateFingerprinter`'s replay hash (extend if a gap is confirmed during Implement).

## Scoped Pytest Commands

```
pytest tests/unit/world/ tests/unit/strategic/ tests/unit/replay/ tests/architecture/ -m "not slow"
```
(widen per the structural test-scope-coverage backstop if Implement touches files outside these
directories — e.g. `tests/unit/core/` if `builder.py`/`strategic.py` change, `tests/certification/`
if `StateFingerprinter` changes, matching both sibling tickets' own precedent.)

## Anti-Drift Test Guards

- A guard test confirming this ticket's displacement logic never touches `identity.faction` (idea
  39's own field) or `LoyaltyDriftService`'s output (idea 56) — these are three independent
  mechanisms sharing the same epic, not one shared trigger.
- A guard test confirming `region.calamity_intensity`'s own read/write semantics are unchanged —
  this ticket only reads it, `CalamityService`/`CalamityPressurePropagator` remain its sole writers.
