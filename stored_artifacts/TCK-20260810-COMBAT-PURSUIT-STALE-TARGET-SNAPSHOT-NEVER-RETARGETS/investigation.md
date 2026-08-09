---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS
artifact_type: investigation
tags: [combat, engine]
---

# Investigation: TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS

## Question
Why does `PURSUIT_ABANDONED` still account for 100% of real `combat_engagement_ended` outcomes
(`dungeon_crawl_seed42_2000t`) even after `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` (COMB-304)
already fixed pursuit to live-retarget from the target's current position instead of a stale
snapshot?

## Method
Direct pipeline instrumentation at 3 levels: (1) a monkeypatched `AuthoritativeApplyPipeline.
refine()` wrapper tracking per-tick positions of a mutually-pursuing pair; (2) a monkeypatched
`MovementCandidateSelector.select()` wrapper logging which entities were selected each tick; (3) a
monkeypatched `MovementPhase.route_movement_intent()` wrapper logging its own computed
`new_position` per entity per tick. All against a real, non-mocked `Kernel.tick_once()` loop.

## Finding
Entities 25 and 12 (`dungeon_crawl_seed42_2000t`) were frozen at exactly Manhattan distance 2.0
(diagonally adjacent, positions (58,60) and (57,59)) for 990+ consecutive ticks. `readiness=100.0`
throughout — not readiness-starved. Tracing `route_movement_intent`'s own per-tick output showed
it successfully moved entity 25 at ticks 8 and 9 (closing distance), then from tick 10 onward
`MovementCandidateSelector.select()` stopped including entity 25 (and 12) in `selected_ids`
entirely — permanently. `route_movement_intent`'s own live-retargeting fix (COMB-304) never got a
chance to run for these entities because `select()`'s own earlier candidacy gate excluded them
first.

Direct inspection of `select()`'s own nav_target computation confirmed the mechanism: it checks
`ent_upd.navigation.target_set` first, falling back to `entity.navigation.target` only if that's
`None` — with NO live-refresh from `task.payload["target_id"]` (unlike `route_movement_intent`,
which COMB-304 already fixed to do exactly this). Once an entity "arrives" at its own stale,
persisted `navigation.target` (`entity.navigation.position == entity.navigation.target`), it's
permanently excluded by `select()`'s own `if nav_target is None or entity.navigation.position ==
nav_target: continue` check — before `route_movement_intent`'s own fix ever runs.

After patching `select()` to also live-refresh (mirroring COMB-304's own logic), entity 25/12
were STILL frozen. Deeper instrumentation of `ent_upd.navigation.target_set` inside `select()`
revealed why: it was ALREADY non-`None` every tick, holding the STALE (58,60) value — meaning
`select()`'s own first branch (`if ent_upd.navigation.target_set is not None: nav_target =
ent_upd.navigation.target_set`) always won, and the new live-refresh fallback (only reached when
`nav_target is None`) was never reached either.

Traced the source of this persistent, stale `target_set`: both real `ENTITY_MOVE` work-item
dispatchers — `executor.py`'s `LocalSequentialExecutor` and `worker_logic.py`'s
`default_simulation_worker` (the latter confirmed, via `Kernel.__init__`'s own executor-selection
logic and `PROD_SMALL`'s own `max_worker_count=2`, to be the REAL dispatch path for this profile)
— re-emit `NavigationUpdate(target_set=item.payload.get("target_position", ...))` EVERY tick a
pursuit task is scheduled (`work_kind=="ENTITY_MOVE"`, which never reclassifies back to
`ENTITY_BRAIN`), reading the SAME static payload snapshot every time. This produces an
`EntityUpdate` with `target_set` always non-`None`, which `route_movement_intent`'s own
`has_fresh_decision = bool(... target_set is not None)` check reads as "this tick has a genuine
new tactical decision" — completely masking the fact that the value never actually changes.

## Root Cause
Two real, independent gaps in COMB-304's own fix, neither in its own original scope:
1. `MovementCandidateSelector.select()` has its own, separate, un-refreshed staleness check that
   runs BEFORE `route_movement_intent`'s per-entity loop.
2. Both real `ENTITY_MOVE` work-item dispatchers reaffirm a stale `target_set` every tick, which
   `route_movement_intent`'s own `has_fresh_decision` check cannot distinguish from a genuine new
   decision.

Either gap alone is sufficient to fully defeat COMB-304's own live-retargeting fix for any entity
that reaches "arrived at stale snapshot" — exactly the state a pursuit reaches before its leash
timeout or stalemate-break mechanic eventually fires `PURSUIT_ABANDONED`.

## Fix
Extracted the live-retargeting logic into `MovementCandidateSelector.resolve_live_tracking_target
(entity, entities, fallback_target)` — a shared static helper taking a plain
`{entity_id: EntityState}` mapping so it works against `AuthoritativeState.entities`,
`WorkerPacket.all_entities`, and `readonly_state.entities` alike. Applied at all 4 real call
sites: `select()`'s own fallback, `route_movement_intent()` (replacing its own inline duplicate),
`LocalSequentialExecutor.execute()`, and `default_simulation_worker`.

## Regression Found and Resolved During Test
`ActionRoutingPhase.route()`'s `is_unrecoverable_attack_failure` reset (`TCK-20260809-COMBAT-
STUCK-ATTACK-TASK-DEAD-TARGET`, earlier this session) conflicts with 2 pre-existing integration
tests expecting `outcome`/`reason` to survive the reset for same-tick atomic-ordering visibility.
Attempted preserving them; live corpus re-verification showed this reintroduces a partial version
of the original stuck-retry bug (73 repeats for one entity in a 2000-tick run, since
`scheduler.py`'s own `is_idle_act` check requires a genuinely empty payload). Reverted to the
original, corpus-verified `payload_set={}}` (0 repeats, confirmed) and updated the 2 tests
instead, since no real production code reads `task.payload.get("outcome")`.

## Verification
Real corpus events: `dungeon_crawl` moved from `{combat_engagement_ended: 10}` only to include
`combat_initiated=1, combat_engagement_started=1, combat_damage=1, entity_killed=1,
combat_resolved=1`; `urban_political` moved from `{combat_engagement_ended: 15}` only to include
`combat_resolved=5`. COMBAT pillar norm moved from exactly 0.0 to -0.0096 on `dungeon_crawl`
(6 real events, grade stayed C — honest, not forced).

## Disclosed, Out-of-Scope Finding
The specific traced pair (25/12) no longer freezes but enters a stable mutual-orbit oscillation
post-fix — a separate, real bug in `NavigationSystem.get_next_step()`'s own single-axis-priority
stepping (never moves diagonally), not touched by this fix. Left as a disclosed follow-up
candidate.
