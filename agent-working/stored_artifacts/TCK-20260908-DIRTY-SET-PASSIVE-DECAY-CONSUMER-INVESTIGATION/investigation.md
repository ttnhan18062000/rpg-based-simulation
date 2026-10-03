---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION
artifact_type: investigation
tags: [determinism]
---

# Investigation — TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION

## Mechanism confirmed
`AuthoritativeApplyPipeline.refine()` (`src/engine/pipeline.py`) rebuilds `update.dirty_set` at 5
checkpoints (lines 321/356/374/389/414), each via `DirtySetBuilder.mark_from_update(state, update)`
(`src/core/dirty.py:115-186`), which reads only `update.entity_updates` — the explicit updates
staged by phases already run this tick. Passive per-entity decay (biological/lifecycle) is computed
entirely inside `ApplyPlanBuilder.build_plan()`'s "candidates" fallback (`src/engine/apply_plan.py:
293-365`), called from `ApplyPath.apply_generation()` — which runs strictly AFTER `refine()`
finishes for the tick, and never produces an `EntityUpdate` object at all (changes are written
directly into `plan.entity_component_changes`/`dirty_tags_by_entity`, an `apply()`-local structure
that never round-trips back into `update.dirty_set`). Confirmed via
`src/engine/apply.py:_compute_entity_changes`'s own "passive" branch (lines 84-160).

## Consumer #1: phase short-circuiting (`src/engine/phase_graph.py`) — CONFIRMED BENIGN

Of the 28 phases in `PhaseDependencyGraph.PHASES`, only two have both (a) `can_skip_when_no_dirty`
true (the dataclass default, never overridden) and (b) `lifecycle` or `biological` in
`input_domains`: `near_death_hardening` ({combat, biological, lifecycle}) and `evolution`
({biological, combat, attributes, inventory}). (`contracts`, the third phase with `lifecycle` in
its domains, runs at pipeline.py:222 — before the first dirty-set checkpoint at line 321, so
`update.dirty_set is None` there and `should_run_phase` always returns True per its own step 4;
it can never actually skip, regardless of this investigation.)

Both `near_death_hardening` (`src/engine/pipeline_phases/hardening.py:47`) and `evolution`
(`src/engine/evolution.py:26`) iterate `update.entity_updates.items()` as their **only** source of
work — neither reads `prior_state.entities` directly. This is the exact same source
`DirtySetBuilder.mark_from_update()` reads to populate the dirty_set in the first place. A
passive-decay-only entity (no `EntityUpdate` staged this tick) is therefore invisible to **both** at
once, by the same root cause — not two independent gaps that happen to coincide. Whenever either
phase would have real relevant work (an entity present in `entity_updates` with `combat`/
`identity`/`reward` set), `mark_from_update` already marks the corresponding domain dirty from that
same entry, so `has_dirty` is already True and the phase does not skip. The skip mechanism can
never discard real, pending work for these two phases specifically.

**Real test evidence** (`tests/unit/engine/test_dirty_set_passive_decay_consumers.py`,
`test_consumer_1_phase_shortcircuit_is_confirmed_benign_not_a_bug`): a real
`AuthoritativeApplyPipeline.refine()` run against an entity already dead in combat (only remaining
change: passive hunger/lifecycle decay, zero `EntityUpdate`) confirms both phases are genuinely
skipped (`metric_counters["skip_near_death_hardening"] == 1`, `skip_evolution == 1`) — and, running
both phases directly (bypassing the skip) on the exact same input produces an identical
`entity_updates` result, proving the skip drops zero real work for this entity, not merely that
none was observed.

**One separate, un-investigated finding, out of this ticket's own scope**: `evolution`'s own
trigger reads `ent_upd.identity` (XP from `evolution_points_delta`) OR `ent_upd.reward` (XP gain),
but `mark_from_update` only marks the phase's own `attributes` domain dirty for `reward` — an
`identity`-only update (no `reward`) is tagged into a separate `identity` domain that
`should_run_phase`'s own `has_dirty` check never inspects. This is a *domain-mapping* gap between
"identity" and "attributes"/"biological", unrelated to the passive-decay omission (it would affect
an explicit, non-passive identity-only update too) — noted for completeness, not investigated
further here per this ticket's own Out of Scope ("any other consumer... not identified in this
investigation's initial scope").

## Consumer #2: read-model invalidation — CONFIRMED BUG, but at a different site than named

The ticket's own Request Summary named `apply_plan.py:72`'s `invalidate_read_model` field. Re-grep
(`grep -rn "invalidate_read_model" --include="*.py" .`) finds it defined and computed in
`apply_plan.py`, and referenced in exactly one place elsewhere — a **comment**, not code, in
`src/domains/combat_engagement/phase.py:171` (corrected in this ticket's own commit — see Files
Changed), originally written under the incorrect assumption that it was live. That assumption
traces back to peer review (`rpg-feature-planning`) itself during an earlier round of this
session's work — the peer independently re-verified the correction against this investigation's
own grep and confirmed it: the field's live-consumer claim was wrong, though the underlying
conclusion it was reasoning toward (stale read-model data is reachable) turned out correct via a
different, real mechanism. It is **never actually read anywhere in the codebase** — dead code,
computed and discarded every tick.

The real, live consumer of this exact gap is one level up: `ReadModelCache.update()`
(`src/api/read_model_cache.py:87-116`) and `ReadModelCache.compute_tick_delta()` (lines 118-151)
both call `ReadModelInvalidationPolicy.get_dirty_entity_ids(dirty_set, ...)`, which reads
`dirty_set.all_dirty_entities` **directly** — completely independent of `apply_plan.py`'s dead
flag. `ReadModelCache` is wired live in `V2EngineManager._update_latest_state()`
(`src/api/engine_manager.py:173-182`), called every tick with `dirty_set =
self._kernel.status.dirty_set` — the exact same published field this ticket investigates — and its
`get_entity_dto()`/`get_entities_paged()` back the real `get_entity`/`get_entities_paged` API
methods (`engine_manager.py:232-244`).

`get_entity_dto()` (`read_model_cache.py:161-174`) is a pure ID-keyed cache with no independent
staleness check: if an entity's ID is not in the tick's `dirty_ids` (from `dirty_set`), its cached
DTO is never popped, and any subsequent read serves the stale, pre-change snapshot until something
*unrelated* eventually marks that entity dirty via a different domain.

**Checked, per peer review**: does anything else evict entries from this cache under pressure,
bounding "indefinitely"? `ReadModelCache.evict_expired()` (lines 60-72) does FIFO-pop stale
entries, but only when called by `CacheRegistry` (`src/engine/cache_registry.py`) on a cache that
was `register_cache()`'d into it. `grep -rn "register_cache\|CacheRegistry(" src/` finds exactly
one registration site anywhere in the codebase — `src/engine/kernel.py:96,99,833`, registering only
`"movement_plan_cache"`. `V2EngineManager`'s own `self._read_cache` (`src/api/engine_manager.py:
43`) is never registered with any `CacheRegistry` instance. So `evict_expired()` never runs against
the live `ReadModelCache` — "indefinitely" is the accurate word for the live path, not an
overstatement (the only other `ReadModelCache()` instantiation anywhere is a throwaway one inside
`src/perf/long_run_harness.py`'s own perf test, unrelated to the live API).

**Real test evidence** (`test_consumer_2_read_model_cache_serves_a_stale_dto_confirmed_bug`): the
same real pipeline/apply run as Consumer #1 (entity already combat-dead, only remaining change:
passive hunger accrual + `lifecycle.active` flip, `dirty_set.all_dirty_entities == set()`) is fed
through a real `ReadModelCache`. The cache is never invalidated for this entity; `get_entity_dto()`
returns the exact stale pre-tick DTO (`hunger: 10.0`) even though the entity's real, committed
`biological.hunger` has since increased. A control test
(`test_consumer_2_full_scan_or_explicit_dirty_tag_avoids_the_staleness`) confirms the same scenario
does NOT go stale when `force_full_scan=True`, isolating the defect to the passive-decay dirty-set
omission specifically, not to `ReadModelCache`'s invalidation logic in general (already covered by
the existing `tests/unit/api/test_read_model_cache.py`).

**Scope note on how narrow this is in practice**: an earlier scenario attempt used a *live*,
critically-wounded entity dying from passive decay for the first time (rather than an
already-combat-dead entity). That scenario failed to isolate the bug: `strategic_intelligence`
(`must_run_every_tick=True`) assigns some goal to essentially any live, cognitively active entity
every tick (`src/ai/goals/scorers.py`'s own hp_ratio-based `COMBAT_RETREAT`/`TOWN_RETURN` fallback
scoring), which produces a same-tick `EntityUpdate` with `strategic`/`navigation` set — marking the
entity dirty via a *different* domain and correctly invalidating its cache entry, incidentally. The
confirmed-stale scenario requires the entity to already be inactive/non-cognitive (dead, or
otherwise excluded from strategic processing) — this narrows, but does not eliminate, the bug's
real blast radius: any entity whose activity has already stopped (death, or any other future
"stops acting" state) but whose passive attribute decay (hunger, sleep_debt, aging) continues will
serve a stale read-model snapshot for those specific fields until something else disturbs it.

## Aside: `BiologicalSystem.update()` is a separate, unwired dead-code path — filed as its own ticket

While tracing the real passive-decay mechanism, found `src/systems/biological_system.py`'s
`BiologicalSystem.update()` — a *different*, explicit-`EntityUpdate`-producing biological decay
implementation (`ent_upd.biological.hunger_delta`, `ent_upd.combat.hp_delta`), covered only by its
own unit test (`tests/unit/core/test_biological.py`) and never called from `src/engine/` or
anywhere else in the live pipeline (`grep -rln "BiologicalSystem" src/ tests/` finds only its own
module, `src/systems/lifecycle_systems/biological.py`, and its own test).

**Per peer review, raised as a real fix-option candidate, not merely a note**: if this module is
the original intended "promote passive decay to a real, dirty-set-visible EntityUpdate" path that
simply never got wired in, then wiring it (or its design) in would make Consumer #2's entire class
of staleness disappear at the source — passive decay would flow through the normal
`update.entity_updates` → `DirtySetBuilder.mark_from_update()` path like everything else, with no
special-casing anywhere, including in `ReadModelCache`. This is NOT asserted as the right fix here
— it is a materially bigger change with its own blast radius (replacing an apply()-time-only,
performance-optimized "candidates" fallback with an explicit per-tick `EntityUpdate` for every
decaying entity has real cost implications, and needs its own investigation into why the codebase
ended up with two parallel decay mechanisms in the first place) — but it must be an explicitly
considered and rejected (or accepted) option in the follow-up fix ticket, not an unexamined
default toward the narrower cache-only patch. Filed as
`TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` (see Related Tickets) so it has its own
scope and doesn't block this investigation's own closure; the follow-up `ReadModelCache` fix
ticket should reference it explicitly when weighing fix approaches.
