---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS
phase: done
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS

## Title
`ReadModelCache` serves stale entity DTOs for entities whose only per-tick change is passive biological/lifecycle decay

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` confirmed a real, live bug:
`ReadModelCache` (`src/api/read_model_cache.py`), wired every tick in
`V2EngineManager._update_latest_state()` (`src/api/engine_manager.py:173-182`) off the published
`kernel.status.dirty_set`, and backing the real `get_entity`/`get_entities_paged` API endpoints
(`engine_manager.py:232-244`), only invalidates a cached entity DTO for IDs present in
`dirty_set.all_dirty_entities`. That published dirty_set is built entirely from
`update.entity_updates` (`DirtySetBuilder.mark_from_update()`, `src/core/dirty.py:115-186`) and
never reflects passive-decay-only entity changes — those are computed later, entirely inside
`ApplyPath.apply_generation()`/`ApplyPlanBuilder.build_plan()`'s "candidates" fallback
(`src/engine/apply_plan.py:293-365`), which never produces an `EntityUpdate` at all.

Confirmed via real pipeline test (`tests/unit/engine/test_dirty_set_passive_decay_consumers.py`,
`test_consumer_2_read_model_cache_serves_a_stale_dto_confirmed_bug`): an entity whose only
per-tick change is passive biological decay (hunger accrual continuing after combat death, before
`lifecycle.active` cleanup) has its cached DTO served stale by `ReadModelCache.get_entity_dto()`
indefinitely — confirmed no eviction pressure exists on the live cache (`ReadModelCache` is never
registered with `CacheRegistry`, so `evict_expired()` never runs against it; only
`"movement_plan_cache"` is registered anywhere in the codebase).

**Scope of the real-world impact, confirmed narrower than "any passive change goes stale"**: a
*live*, cognitively-active entity dying from passive decay for the first time is NOT affected in
practice — `strategic_intelligence` (`must_run_every_tick=True`) assigns some goal to essentially
any live entity every tick (`src/ai/goals/scorers.py`'s own hp_ratio-based `COMBAT_RETREAT`/
`TOWN_RETURN` fallback scoring), incidentally marking it dirty via a different domain. The bug
reproduces specifically for entities that have already stopped acting (death, or any future
"stops acting" state) but whose passive attribute decay (hunger, sleep_debt, aging) continues.

**UPDATE 2026-09-12 (pre-pickup Scope correction, not an Investigate-phase finding)**: the
"materially different fix-approach option" paragraph below is now obsolete.
`TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` closed via PR #163
(`66e40f197`, "Delete 3 confirmed-dead code paths: BiologicalSystem, spawn_calamity(),
effective_certainty()"): `BiologicalSystem.update()` was confirmed a **superseded** implementation,
not a missing/unwired one — direct code comparison showed it and `apply.py`'s own live passive
decay path compute the same job with materially different numbers and different applicability
scope, and the class (plus its shim and orphaned test file) was deleted outright. There is no
longer a "wire the dormant system in" option to weigh — `src/systems/biological_system.py` no
longer exists. This ticket's own default/fallback fix approach (the cache-local supplementary
dirty-id source, described below) is now the only real option, not a fallback contingent on that
disposition. The paragraph and Scope bullet below are left in place, struck through in spirit but
not edited out, so the ticket's own history is traceable; treat the "UPDATE" note above as
authoritative over them.

~~**A materially different fix-approach option must be explicitly weighed, not defaulted past**: see
`TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` — `src/systems/biological_system.py`'s
`BiologicalSystem.update()` is a dormant, unwired, explicit-`EntityUpdate`-producing biological
decay implementation. If wiring it in (replacing or supplementing the apply()-time-only passive
path) is the original design intent, it would eliminate this entire class of staleness at the
source rather than patching the cache. That disposition ticket must close (or at least reach a
provisional finding) before this ticket picks its own final fix approach.~~

## Scope
- ~~Read `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`'s own finding first — if it
  recommends wiring `BiologicalSystem.update()` in as a real option, this ticket's Investigate
  phase must weigh it seriously (cost of wiring vs. cost of a cache-local patch) before defaulting
  to the narrower fix below.~~ **Obsolete as of 2026-09-12** — that disposition ticket closed via
  PR #163: `BiologicalSystem.update()` was confirmed superseded (not missing/unwired) and deleted
  outright. There is nothing left to read or weigh; go straight to the fix approach below.
- **The fix approach (was described as "default/fallback"; now the only real option since the
  dormant-system-wiring alternative no longer exists — see the 2026-09-12 note above)**: give
  `ReadModelCache` a supplementary
  post-apply dirty-id source, independent of the shared `update.dirty_set` (which Consumer #1's own
  confirmed-benign finding means does NOT need to change for phase-gating reasons). Concretely:
  surface `ApplyPlan.dirty_tags_by_entity` (`src/engine/apply_plan.py:44`, currently computed but
  apply()-local-only) out of `ApplyPath.apply_generation()` in some form (a return value, a status
  field, or similar — determine the least invasive plumbing during Investigate) and feed it into
  `ReadModelCache.update()`/`compute_tick_delta()` as an additional invalidation-id source, without
  widening what `update.dirty_set` itself means for every other consumer (phase gating, movement
  cache, etc.).
- Do not touch the shared `update.dirty_set`'s own publication semantics or `PhaseDependencyGraph`'s
  own skip logic — Consumer #1 is confirmed benign; this fix must not reintroduce risk there.
- Real test evidence the staleness is fixed: the exact scenario in
  `test_dirty_set_passive_decay_consumers.py`'s `test_consumer_2_read_model_cache_serves_a_stale_dto_confirmed_bug`
  should be updated (or a new test added) to assert the DTO is now correctly invalidated.

## Out of Scope
- `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION`'s own Consumer #1 finding
  (phase short-circuiting) — confirmed benign, not reopened here.
- ~~Wiring `BiologicalSystem.update()` in — that belongs to
  `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` and, if accepted as the chosen fix
  approach, its own follow-up implementation ticket; this ticket only needs to weigh it as an
  option, not necessarily implement it.~~ **Moot as of 2026-09-12**: `BiologicalSystem.update()`
  and its containing module no longer exist (deleted by PR #163 as confirmed-superseded). Nothing
  to wire, nothing to weigh.
- Any performance work distinct from correctness. Per standing user direction (2026-09-08), only
  hard failures are fixed; anything found that is "correct but slower" is deferred to the planned
  performance effort.

## Acceptance Criteria
- [x] ~~`TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`'s finding is read and explicitly
      weighed (accepted or rejected with rationale) before choosing this ticket's own fix
      approach.~~ Satisfied by this 2026-09-12 Scope update: that ticket closed via PR #163
      (`BiologicalSystem.update()` deleted as confirmed-superseded), so there is no option left to
      weigh — the cache-local fix approach is the only one.
- [x] A real fix is implemented that makes `ReadModelCache` correctly invalidate entities whose
      only per-tick change is passive decay, without widening `update.dirty_set`'s own semantics
      for other consumers. Done via a declared, non-authoritative `_apply_time_dirty_set` field on
      `AuthoritativeState`, populated unconditionally by `ApplyPath.apply_generation()` and read
      directly by `ReadModelCache.update()`/`compute_tick_delta()` as a second, independent source.
      `update.dirty_set`'s own type and every other consumer's read of it are unchanged.
- [x] Real test evidence: the existing repro test in `test_dirty_set_passive_decay_consumers.py`
      is updated to confirm the fix, and passes. Renamed
      `test_consumer_2_read_model_cache_invalidates_passive_decay_only_change`; now asserts the
      cache serves a fresh DTO with the real accrued hunger, not the stale pre-tick snapshot.
- [x] No regression in `tests/unit/api/test_read_model_cache.py`,
      `tests/unit/domains/optimization/test_phase_dependency_graph.py`, or `tests/unit/engine/`.
      231 passed, 1 skipped. Also verified `tests/unit/core/`, `tests/unit/api/` (305 passed) and
      the determinism/replay suites (5 passed) given the change touches `AuthoritativeState`'s own
      dataclass shape.

## Related Tickets
- `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` (origin; confirmed both findings)
- `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` (closed via PR #163 — `BiologicalSystem.
  update()` deleted as confirmed-superseded; no longer a live dependency, see 2026-09-12 Scope note)

## Related Docs
None yet.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS/`
  (`investigation.md`, `plan.md`, `test_plan.md`)

## Related Code Areas
- `src/api/read_model_cache.py` (`ReadModelCache.update()`, `get_entity_dto()`,
  `compute_tick_delta()`, `ReadModelInvalidationPolicy`)
- `src/api/engine_manager.py` (`V2EngineManager._update_latest_state()`, the live wiring point)
- `src/engine/apply_plan.py` (`ApplyPlan.dirty_tags_by_entity`, apply()-local, source of truth)
- `src/engine/apply.py` (`ApplyPath.apply_generation()`, where `_apply_time_dirty_set` is now
  computed unconditionally and stashed on the returned state)
- `src/core/state.py` (`AuthoritativeState._apply_time_dirty_set`, the new declared field)
- ~~`src/systems/biological_system.py` (the dormant alternative — see
  `BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`)~~ **Deleted by PR #163** — no longer exists.

## Assumptions / Open Questions
- ~~The final fix approach (cache-local patch vs. wiring the dormant `BiologicalSystem`) is
  deliberately not decided here — left for Investigate, informed by the disposition ticket.~~
  **Resolved as of 2026-09-12**: the dormant-`BiologicalSystem` option no longer exists (PR #163).
  The cache-local supplementary dirty-id source is the fix approach; Investigate should confirm the
  least-invasive plumbing shape, not re-litigate which approach to take.

## Implementation Notes
Brought the concrete plumbing shape to peer review before implementing, per standing instruction:
a separate channel for `ReadModelCache`, not a widening of `update.dirty_set`'s own meaning. Peer
review corrected one detail — the `_readonly_entities_cache` pattern I cited as precedent is a
real declared dataclass field, not an undeclared post-construction stash — and had me follow that
precedent completely rather than partially, to avoid the exact silent-loss failure class that lost
`places` for every tick until a prior hotfix (`TCK-20260908-HOTFIX-STATE-PLACES-APPLY-CARRYFORWARD-
GAP`).

Declared `_apply_time_dirty_set: Any = field(default=None, repr=False, compare=False)` on
`AuthoritativeState` (`src/core/state.py`), reset in `__post_init__` so any construction path other
than `apply_generation()` can't carry forward a stale value, and added it to `to_readonly()`'s own
explicit carry-forward list (`replace(self, ...)`) — a carry-forward this fix would otherwise have
silently missed on any code path that calls `.to_readonly()`, the same failure class flagged above.

In `ApplyPath.apply_generation()` (`src/engine/apply.py`), the local `dirty_builder`'s
`build()` call — previously only invoked when an `audit_dirty_set` collector was passed, which no
real caller (of the five real `apply_generation()` call sites, confirmed by peer review's own
count, not the three initially assumed) ever does — is now always computed and stashed onto the
returned state via `object.__setattr__`, mirroring `_readonly_entities_cache`'s own post-
construction assignment two lines above.

`ReadModelCache.update()` and `compute_tick_delta()` (`src/api/read_model_cache.py`) both read
`state._apply_time_dirty_set` directly (not `getattr(..., None)` — per peer review, a declared
field with a default is always safe to access directly, and direct access fails loudly instead of
silently degrading if the field is ever removed) and union its `all_dirty_entities` into their own
locally-computed dirty-id set when present and not already doing a full scan.
`ReadModelInvalidationPolicy.get_dirty_entity_ids()` and `update.dirty_set`'s own type are
completely untouched — confirmed by the updated repro test, which asserts the published pre-apply
`dirty_set` for the exact scenario stays empty (unchanged) while the fix still correctly
invalidates via the new supplementary source.

Considered and rejected a return-type change to `apply_generation()` as an alternative plumbing
shape (surfacing the dirty set as part of the function's own return value) — peer review's count of
five real call sites made this materially more invasive than the declared-field approach, for the
same discoverability.

## Test Summary
Updated `tests/unit/engine/test_dirty_set_passive_decay_consumers.py`'s own repro test (renamed
`test_consumer_2_read_model_cache_invalidates_passive_decay_only_change`, dropping the "confirmed
bug" framing now that it's fixed) to assert the DTO is correctly invalidated and reflects the real
accrued hunger. All 4 tests in that file pass. The ticket's own named regression scope
(`tests/unit/api/test_read_model_cache.py`, `tests/unit/domains/optimization/
test_phase_dependency_graph.py`, `tests/unit/engine/`) — 231 passed, 1 skipped. Broader sanity
sweep given the change touches `AuthoritativeState`'s own dataclass shape and
`apply_generation()`'s hot path: `tests/unit/core/test_authoritative_state_contract.py` +
`tests/unit/engine/test_hash_scheduler.py` (24 passed), `tests/unit/core/` + `tests/unit/api/` (305
passed), `tests/integration/kernel/test_determinism_suite.py` + `tests/unit/kernel/
test_replay_determinism.py` (5 passed, confirms the new `compare=False` field doesn't affect the
determinism hash).

## Files Changed
- `src/core/state.py` — declared `_apply_time_dirty_set` field; reset in `__post_init__`; carried
  forward in `to_readonly()`.
- `src/engine/apply.py` — `dirty_builder.build()` now computed unconditionally; result stashed on
  `new_state`.
- `src/api/read_model_cache.py` — `update()` and `compute_tick_delta()` both union in the new
  supplementary source.
- `tests/unit/engine/test_dirty_set_passive_decay_consumers.py` — updated the repro test to assert
  the fix.
- `tickets/todos/TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS.md` — the pre-pickup Scope
  update (committed separately, already landed in PR A / #174 before this ticket was picked up).
- `stored_artifacts/TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS/{investigation.md,plan.md,test_plan.md}`
  — full evidence trail.
- `tickets/done/TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS.md` — this file, closed.

## Completion Summary
Fixed the confirmed staleness bug: `ReadModelCache` now correctly invalidates cached entity DTOs
for entities whose only per-tick change is passive biological/lifecycle decay. The pre-pickup Scope
update (this ticket's own dependency on `BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`, resolved via PR
#163) confirmed the cache-local fix was the only real option, not a fallback.

The plumbing shape — a declared `_apply_time_dirty_set` field on `AuthoritativeState`, populated
unconditionally by `ApplyPath.apply_generation()` and read directly by `ReadModelCache` as a second,
independent invalidation source — was proposed and brought to peer review before implementation,
per standing instruction. Peer review's correction (follow the `_readonly_entities_cache` precedent
completely, as a real declared field rather than an undeclared stash) closed off the exact silent-
loss failure mode that has recurred in this codebase before (`places` being lost for every tick
until a prior hotfix). `update.dirty_set`'s own publication semantics, and every other consumer
that reads it (phase gating, movement cache), are completely unchanged — confirmed by the updated
regression test, which asserts the published pre-apply dirty_set stays empty for the exact
scenario while the fix still correctly invalidates via the new supplementary source.

`apply_plan.py`'s own `invalidate_read_model` hint field remains confirmed dead (out of this
ticket's scope, not addressed) — a separate finding if anyone wants it revisited later.
