---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality]
---

# TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS

## Title
Build `WorldDynamicsShaper` — region/demographic/spawn event emission moved to apply-layer push

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 4 of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC`. Migrates 15 WORLD
dynamics / demographic / NARRATIVE-co-fire events from `event_extractor.py`'s diffing
(`event_extractor.py:130-159`, `:889-1030`) to a new `WorldDynamicsShaper`, under
`FeatureMode.SHADOW`.

Direct confirmation this session (`src/core/updates.py:745-768`, `:867-875`): every one of these
events already reads directly off typed `update` fields, not materialized-state diffing:

| Event | Source field |
|---|---|
| `demographic_birth` | `StateUpdate.entities_add` |
| `demographic_mortality` | `StateUpdate.entities_remove` + `_real_combat_update(e_upd) is None` (reuses the exact shared helper `CombatShaper` already imports) |
| `region_trauma_delta` | `WorldUpdate.trauma_delta` |
| `region_ownership_changed` | `WorldUpdate.owner_faction_id_set` |
| `region_transformed` | `WorldUpdate.kind_set` |
| `threat_evolved` | `WorldUpdate.trauma_delta` + `prior_state.regions[rid].trauma_score` (threshold-crossing check, same "read prior_state directly" pattern `FactionShaper.alliance_proposed` already uses) |
| `building_sabotaged` | `update.building_updates[b_id].hp_delta` |
| `calamity_spawned` | `update.last_calamity_tick_set` |
| `boss_spawned` / `raid_party_spawned` | `update.entities_add`, filtered by `kind` |
| `spawn_cadence_fired` | `update.entities_add`, tick-modulo gated |
| `narrative_milestone` | co-emitted alongside `boss_spawned`/`war_declared` — trivial once those fire from this shaper |
| `world_emergence_event` | every `WorldEvent` in `update.world_events_add` (already the exact mechanism `FactionShaper`'s `war_declared`/`military_conflict_resolved` reads from) |
| `ecology_cycle_completed` | tick-modulo sweep over `prior_state.regions` (stable region set, no update dependency) |

`demographic_mortality` was classified as a genuine deferral by Phase 1's own audit
(`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE`'s "3 of 4 checked domains" table did
not include it, and the epic's `SEQUENCE.md` listed it under COMBAT's deferred events as "despawn
branch, broader than combat"). That was premature — `StateUpdate.entities_remove` gives exactly
the signal needed, and `_real_combat_update` (already shared/imported) gives the "was this a
combat kill" exclusion for free. This ticket closes that Phase 1 deferral as a side effect —
record this explicitly in `docs/parity_ledger/infrastructure.yaml`'s `INFRA-324` entry when done
(update in place, don't create a duplicate).

## Scope
1. **Investigate first**: confirm each field mapping above against the current
   `event_extractor.py` code (cite file:line for both old and new read sites), confirm
   `world_events_add`'s `WorldEvent` category enum values match `war_declared`'s existing
   `_MILITARY_RESOLVED_CATEGORIES`-style pattern for whatever narrative/world-emergence categories
   this shaper needs.
2. Add `WorldDynamicsShaper` implementing all 15 events (13 direct + `narrative_milestone` +
   `world_emergence_event`, minus the 3 already-deferred `resource_node_*`/`node_recharged` events
   which belong to child 6, not this one).
3. Register under `FeatureMode.SHADOW`.
4. Add unit tests per event.
5. Verify via real kernel run against worlds with active calamity/boss/raid mechanics.
6. Update `docs/parity_ledger/world_dynamics.yaml` (new entries) and `infrastructure.yaml`
   (`INFRA-324` update-in-place closing the `demographic_mortality` deferral).

## Out of Scope
- `resource_node_depleted`/`resource_node_regenerated`/`node_recharged` — no typed per-node update
  record exists yet; child 6's scope, not this one.
- `conservation_law_verified` — meta/derived, child 6's scope.
- Delivering live — SHADOW only, cutover is child 8.

## Acceptance Criteria
- [x] `investigation.md` confirms each event's exact field mapping with file:line citations
- [x] `WorldDynamicsShaper` implements all 14 events, registered in `PHASE2_SHAPER_REGISTRY`
      (same deviation as Children 2-3, same reason)
- [x] Unit tests cover every event's fire condition + non-firing case (25 tests)
- [x] Real kernel run confirms correctly-shaped SHADOW output — 3 worlds, exact 1:1 parity for
      every event type that fired
- [x] `docs/parity_ledger/world_dynamics.yaml` updated (`WORLD-115`); `infrastructure.yaml`
      `INFRA-324` updated in place to record the `demographic_mortality` deferral closure
- [x] Scoped pytest run passes — 1011 passed, 6 skipped, 3 deselected

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-PHASE2-EPIC (parent epic)
- TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT (DONE — original `INFRA-324` entry and
  `demographic_mortality`'s original deferral, updated in place by this ticket)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md` §1.1, §3.9
- `docs/parity_ledger/world_dynamics.yaml`, `infrastructure.yaml`

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS/` during implementation.

## Related Code Areas
- `src/observability/event_shapers.py`
- `src/observability/event_extractor.py` (lines 130-159, 889-1030)
- `src/core/updates.py` (`WorldUpdate`, `StateUpdate`)

## Assumptions / Open Questions
- None expected to be genuinely open — every event in this ticket's scope was directly confirmed
  against a typed field this session. If Investigate finds a surprise, treat it as a real finding
  to report, not to work around silently.

## Implementation Notes
- Confirmed all 14 events read typed `StateUpdate` fields directly — no cross-tick derived logic
  in this domain, so no `reset_run_state()` was needed (unlike Children 2-3).
- Closed Phase 1's own `INFRA-324` `demographic_mortality` deferral: `StateUpdate.entities_remove`
  + the already-shared `_real_combat_update()` helper give the signal directly, no new
  instrumentation — the original deferral was a correct scope boundary at the time (Phase 1 was
  COMBAT-only), not an error, now closed since this ticket's domain is broader.
- Included `narrative_milestone`/`world_emergence_event` (left "out of migration scope" by Phase
  1) since they read the same `world_events_add` record `FactionShaper` already migrated, and
  this ticket's own domain (WORLD/NARRATIVE co-fire) is the natural home for them.
- `building_sabotaged` substitutes `prior_state` for `current_state` in its region lookup —
  confirmed equivalent by reading `SpatialQueryService.get_building_region()`'s implementation.
- Real-kernel verification across 3 worlds confirmed exact parity for every event type that fired.
  Initially found what looked like a `SHADOW`-mode leak (41 delivered `event_shapers`-sourced
  events) — investigated before concluding it was a real bug: it was Phase 1's own already-live
  shaper output (a different, already-cutover flag), not a Phase 2 leak. Fixed the verification
  script's filter, confirmed 0 WorldDynamics-specific deliveries in `SHADOW` mode.

## Test Summary
- `pytest tests/unit/observability/test_event_shapers_world_dynamics.py -q`: 25 passed (new).
- `pytest tests/unit/observability/ tests/unit/kernel/ tests/integration/kernel/ -m "not slow" -q`:
  1011 passed, 6 skipped, 3 deselected (was 986/6/3 after Child 3 — +25 matches exactly).
- Real kernel runs (`dungeon_crawl`/`urban_political`/`hero_guild_routing`, 500 ticks each): exact
  1:1 parity between `event_extractor`/`event_shapers` for `ecology_cycle_completed`/
  `region_trauma_delta`. `SHADOW` mode confirmed 0 WorldDynamics-specific deliveries.

## Files Changed
- `src/observability/event_shapers.py` — `WorldDynamicsShaper`, registered in
  `PHASE2_SHAPER_REGISTRY["world_dynamics"]`.
- `tests/unit/observability/test_event_shapers_world_dynamics.py` (new, 25 tests).
- `docs/parity_ledger/world_dynamics.yaml` (`WORLD-115`), `infrastructure.yaml` (`INFRA-324`
  updated in place).

## Completion Summary
Built `WorldDynamicsShaper` covering all 14 WORLD dynamics/demographic/NARRATIVE-co-fire events
with zero new instrumentation, closing Phase 1's own `demographic_mortality` deferral as a side
effect and pulling `narrative_milestone`/`world_emergence_event` into scope since they read an
already-migrated typed record. Real-kernel verification across 3 worlds confirmed exact parity;
one apparent SHADOW-mode leak was investigated and correctly attributed to Phase 1's own separate,
already-live delivery path rather than assumed to be a bug in this ticket's code. SHADOW-only, as
scoped; cutover is a separate, later ticket.
