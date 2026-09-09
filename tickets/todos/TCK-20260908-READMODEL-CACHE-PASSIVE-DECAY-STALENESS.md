---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS
phase: open
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS

## Title
`ReadModelCache` serves stale entity DTOs for entities whose only per-tick change is passive biological/lifecycle decay

## Status
OPEN

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

**A materially different fix-approach option must be explicitly weighed, not defaulted past**: see
`TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` — `src/systems/biological_system.py`'s
`BiologicalSystem.update()` is a dormant, unwired, explicit-`EntityUpdate`-producing biological
decay implementation. If wiring it in (replacing or supplementing the apply()-time-only passive
path) is the original design intent, it would eliminate this entire class of staleness at the
source rather than patching the cache. That disposition ticket must close (or at least reach a
provisional finding) before this ticket picks its own final fix approach.

## Scope
- Read `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`'s own finding first — if it
  recommends wiring `BiologicalSystem.update()` in as a real option, this ticket's Investigate
  phase must weigh it seriously (cost of wiring vs. cost of a cache-local patch) before defaulting
  to the narrower fix below.
- **Default/fallback approach (per the investigation ticket's own peer-reviewed recommendation),
  if wiring the dormant system is rejected or deferred**: give `ReadModelCache` a supplementary
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
- Wiring `BiologicalSystem.update()` in — that belongs to
  `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` and, if accepted as the chosen fix
  approach, its own follow-up implementation ticket; this ticket only needs to weigh it as an
  option, not necessarily implement it.
- Any performance work distinct from correctness. Per standing user direction (2026-09-08), only
  hard failures are fixed; anything found that is "correct but slower" is deferred to the planned
  performance effort.

## Acceptance Criteria
- [ ] `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`'s finding is read and explicitly
      weighed (accepted or rejected with rationale) before choosing this ticket's own fix approach.
- [ ] A real fix is implemented that makes `ReadModelCache` correctly invalidate entities whose
      only per-tick change is passive decay, without widening `update.dirty_set`'s own semantics
      for other consumers (unless the chosen approach is "wire `BiologicalSystem.update()` in,"
      in which case this constraint doesn't apply — record the rationale either way).
- [ ] Real test evidence: the existing repro test in `test_dirty_set_passive_decay_consumers.py`
      is updated to confirm the fix, and passes.
- [ ] No regression in `tests/unit/api/test_read_model_cache.py`,
      `tests/unit/domains/optimization/test_phase_dependency_graph.py`, or `tests/unit/engine/`.

## Related Tickets
- `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` (origin; confirmed both findings)
- `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` (must be read before choosing a fix
  approach here — see Scope)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/api/read_model_cache.py` (`ReadModelCache.update()`, `get_entity_dto()`,
  `compute_tick_delta()`, `ReadModelInvalidationPolicy`)
- `src/api/engine_manager.py` (`V2EngineManager._update_latest_state()`, the live wiring point)
- `src/engine/apply_plan.py` (`ApplyPlan.dirty_tags_by_entity`, currently apply()-local)
- `src/engine/apply.py` (`ApplyPath.apply_generation()`, where the supplementary id source would
  need to be surfaced from)
- `src/systems/biological_system.py` (the dormant alternative — see
  `BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`)

## Assumptions / Open Questions
- The final fix approach (cache-local patch vs. wiring the dormant `BiologicalSystem`) is
  deliberately not decided here — left for Investigate, informed by the disposition ticket.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
