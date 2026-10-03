---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS
artifact_type: investigation
tags: [observability, engine, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS

## Current Behavior — field-mapping confirmation

Confirmed all 14 events' exact source, per `event_extractor.py:130-159,889-1030,1108-1186`:

| Event | Source field |
|---|---|
| `demographic_birth` | `StateUpdate.entities_add` |
| `demographic_mortality` | `StateUpdate.entities_remove` + `_real_combat_update(e_upd) is None` (shared helper) — closes Phase 1's `INFRA-324` deferral |
| `ecology_cycle_completed` | tick-modulo sweep over `prior_state.regions` (stable set, no update dependency) |
| `spawn_cadence_fired` | tick-modulo + `entities_add`, filtered by kind |
| `threat_evolved` | `WorldUpdate.trauma_delta` + `prior_state.regions[rid].trauma_score` threshold-crossing |
| `building_sabotaged` | `update.building_updates[b_id].hp_delta` |
| `region_ownership_changed` | `WorldUpdate.owner_faction_id_set` |
| `region_transformed` | `WorldUpdate.kind_set` |
| `region_trauma_delta` | `WorldUpdate.trauma_delta` |
| `calamity_spawned` | `update.last_calamity_tick_set` |
| `boss_spawned` / `raid_party_spawned` | `entities_add`, filtered by kind |
| `narrative_milestone` (boss variant) | co-emitted with `boss_spawned` |
| `narrative_milestone` (war/sovereignty variant) | `update.world_events_add`, same record `FactionShaper` already reads |
| `world_emergence_event` | every `WorldEvent` in `update.world_events_add` |

`narrative_milestone`/`world_emergence_event` were left "out of migration scope" by Phase 1
(COMBAT/ECONOMY/FACTION only) — not because they weren't push-ready (they read the exact same
`world_events_add` record `FactionShaper` already migrated), just because NARRATIVE wasn't Phase
1's domain. Included here since they're WORLD/NARRATIVE-adjacent and this ticket's own domain.

`building_sabotaged` substitutes `prior_state` for the old extractor's `current_state` in its
`SpatialQueryService.get_building_region()` call — confirmed equivalent by reading that function's
implementation (`src/engine/spatial_query.py:239-243`): reads `state.buildings` (position data),
which sabotage never changes (only HP), so a prior-tick lookup gives an identical result for any
building that already existed.

## `demographic_mortality` — closing Phase 1's own deferral

Phase 1's `INFRA-324` classified this as "despawn branch, broader than combat," deferred rather
than migrated. Re-examined here: `StateUpdate.entities_remove: List[int]` (confirmed
`src/core/updates.py:875`) gives exactly the "this entity was removed this tick" signal, and the
already-shared `_real_combat_update()` helper gives the "was this a combat kill" exclusion for
free — no new instrumentation needed. This was simply not checked closely enough during Phase 1's
own COMBAT-scoped investigation (a legitimate scope boundary at the time, not an error), now
resolved as part of this ticket's own event coverage per the epic's own `SEQUENCE.md`.

## Verification

Real, non-mocked kernel runs across 3 worlds (`dungeon_crawl`, `urban_political`,
`hero_guild_routing`, 500 ticks each): `ON` mode showed exact 1:1 parity between
`event_extractor` and `event_shapers` source counts for every event type that fired
(`ecology_cycle_completed`, `region_trauma_delta` in all 3 worlds). Other events
(`demographic_birth`/`mortality`, `threat_evolved`, `calamity_spawned`, `boss_spawned`, etc.) did
not fire in any of the 3 runs within 500 ticks — consistent with `event_type_coverage.md`'s own
documented rarity for several of these in short calibration runs; unit tests (mocked) directly
verify each event's fire condition regardless of real-corpus frequency.

`SHADOW` mode verification initially appeared to show 41 delivered `event_shapers`-sourced
events — investigated before concluding it was a bug, not assumed: the 41 were Phase 1's own
already-live `CombatShaper`/`FactionShaper` events (`hazard_drain_applied`,
`diplomatic_transition`, `combat_initiated`), correctly delivered via the separate, already-ON
`ENABLE_PUSH_EVENT_SHAPERS` flag — a flaw in the verification script's own filter (checked all
`event_shapers`-sourced events, not `WorldDynamicsShaper`-specific ones), not a real bug. Refixed
the check to filter by this ticket's own 14 event types: confirmed 0 delivered in `SHADOW` mode.

## Docs Requiring Update

- `docs/parity_ledger/world_dynamics.yaml`: new entry for the shaper build.
- `docs/parity_ledger/infrastructure.yaml`: `INFRA-324` updated in place, closing the
  `demographic_mortality` deferral.

## Parity Ledger Overlap

`world_dynamics.yaml` (new entry), `infrastructure.yaml` (`INFRA-324`, update in place).

## Prior Work

- `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT` (Phase 1, DONE) — original `INFRA-324` entry and the
  `demographic_mortality` deferral this ticket closes.
- `TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY`/`-PROGRESSION` (Phase 2, DONE) — the
  `PHASE2_SHAPER_REGISTRY`/flag-split mechanism this ticket reuses; the any-update-vs-specific-
  update-gating pattern was checked explicitly here too (see below).

## Risks and Open Questions

None left open. Explicitly checked for the any-update-gating gap (Children 2/3's recurring
finding) — none of this ticket's 14 events need it: `demographic_mortality`/`demographic_birth`
key off `entities_remove`/`entities_add` directly (not a per-entity `EntityUpdate` sub-record),
and every other event reads `world_updates`/`building_updates`/`world_events_add`/tick-modulo
directly, with no cross-tick "did nothing change but time passed" case like `belief_stale`/
`progression_plateau_detected` had.

## Anti-Drift Hazards

- `WorldDynamicsShaper` has no per-run dedup cache, unlike `StrategyShaper`/`ProgressionShaper` —
  no `reset_run_state()` needed, confirmed by checking every event's condition is purely
  this-tick-derived (tick-modulo or direct field presence), not cross-tick accumulated.
