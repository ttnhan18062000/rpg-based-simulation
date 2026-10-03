---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION
phase: done
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION

## Title
Determine whether the published dirty_set's omission of passive-decay-only entity changes causes real phase-skip or read-model-staleness bugs

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Split out of `TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-DEACTIVATE-RECOLOR-GAP`, which fixed a
rendering symptom of a structural gap without touching the gap itself. The gap: the published
`dirty_set` — the single field both `Kernel._run_hard_law_checks`/`kernel._status.dirty_set` and
several pipeline consumers read — is finalized by `AuthoritativeApplyPipeline.refine()`
(`src/engine/pipeline.py:56-58`, via `DirtySetBuilder(update.dirty_set)` / `mark_from_update`)
**before** `ApplyPath.apply()`/`ApplyPlanBuilder.build_plan()` ever runs. It is built entirely from
`update.entity_updates` — the explicit updates submitted by that tick's active phases. But
`ApplyPlanBuilder.build_plan()`'s own "candidates" fallback (`src/engine/apply_plan.py:299-314`)
computes and applies additional **passive** per-entity state changes (biological decay, aging, and
critically, the post-death `lifecycle.active` cleanup flip, `src/engine/apply.py:109`) for entities
that have **no** corresponding entry in `update.entity_updates` at all — a dead entity stops acting,
so its only remaining state changes come from this passive path. Those changes get applied to the
real, committed state and get their own `plan.dirty_tags_by_entity` entry (`apply_plan.py:363`), but
that only feeds a separate, `apply()`-local `DirtySetBuilder()` instance
(`src/engine/apply.py:234,264-265`) used solely for audit validation against the pre-existing
`dirty_set` (`apply.py:496-497`) — it never updates the actual published `update.dirty_set`.

Concretely confirmed via direct instrumentation (see the sibling hotfix ticket's Implementation
Notes for the full trace): an entity that dies in real combat (tick N, correctly dirty-tracked via
its explicit `EntityUpdate`) later deactivates one tick afterward purely via passive decay (tick
N+1) — and that tick's published `dirty_set` does **not** include this entity, even though its
persisted `lifecycle.active` state demonstrably flips at that exact tick boundary.

**Peer review (`rpg-feature-planning`) independently identified and I independently verified two
real consumers of this same published `dirty_set` that could be affected by this omission — and
sharpened the framing of the more serious one:**

1. **`src/engine/phase_graph.py:127-150` (phase short-circuiting).** A phase whose `input_domains`
   includes e.g. `"lifecycle"` and whose `can_skip_when_no_dirty` is set gets skipped for the
   **entire tick** if `ds.lifecycle_entities` is empty — checked once per domain, not per entity.
   This means the skip is **tick-wide, not per-entity**: if the *only* lifecycle-domain change on a
   given tick, across every entity in the world, happens to be a passive-decay-only change (no
   entity had an explicit lifecycle-tagged `EntityUpdate` that tick), the entire phase is silently
   skipped for that tick — not just skipped for the one passively-decaying entity. This is a
   materially different (and more serious) claim than "one entity's render is stale" — it is a real
   correctness question about whether a lifecycle-consuming phase can silently not run on a tick
   where it should have.
2. **`src/engine/apply_plan.py:72` (read-model invalidation).**
   `invalidate_read_model = update.dirty_set is not None and bool(all_dirty_entities)` — if
   `all_dirty_entities` is empty on a tick where a real change was nonetheless applied (the passive-
   decay-only case), the read model is not invalidated. This is API/HUD-visible staleness, not
   merely a debug-render artifact.

A third candidate the peer initially raised, `apply_plan.py:71`'s `invalidate_movement_cache`, was
checked and ruled out — it reads only `update.dirty_set is not None`, never the set's contents, so
it cannot be affected by an under-reported (but still present) dirty set. **This ticket's
investigation scope is therefore exactly the two consumers above, not three.**

## Scope
- **Investigation only, evidence-based, not reasoning-based** — for each of the two consumers:
  1. Construct or identify a real scenario where a tick's *only* relevant dirty-domain change is a
     passive-decay-only entity mutation (no entity has an explicit `EntityUpdate` touching that
     domain that tick).
  2. For phase short-circuiting: determine, with a real test against the actual pipeline (not a
     synthetic unit stub), whether a phase gated on that domain is actually skipped on such a tick,
     and whether that skip has an observable behavioral consequence (a state change that should have
     happened but didn't, or a downstream test that fails/would fail if the skip is real).
  3. For read-model invalidation: determine, with a real test, whether a read model actually goes
     stale (serves data that has diverged from the true `AuthoritativeState`) for at least one tick
     following such a passive-decay-only change.
- Produce a clear finding for each consumer: **confirmed bug**, **confirmed benign** (with the
  mechanism that makes it benign — e.g. another domain's dirty tag always coincides in practice, or
  the phase re-runs on the very next tick anyway with no observable gap), or **inconclusive** (with
  what evidence would resolve it).
- **Only if at least one consumer is confirmed a real bug**: propose and get a design decision
  (`AskUserQuestion`/peer-routed per this repo's standing decision-routing convention) on the fix
  approach before implementing it. The two live implementation options: (a) publish
  `plan.dirty_tags_by_entity` into the actual `update.dirty_set` returned from `ApplyPath.apply()`,
  changing what `dirty_set` means for every consumer at once, including phase gating — an
  architecturally significant, determinism-relevant change requiring its own Verify pass; or
  (b) a narrower fix scoped to only the confirmed-affected consumer(s), if their gate can be
  satisfied without changing the shared `dirty_set` publication contract itself.

## Out of Scope
- Implementing any fix without first confirming the bug is real (do not lead with the dirty-set
  publication change, per the sibling hotfix ticket's own explicit reasoning for splitting this out).
- `src/rendering/incremental.py` / the render-path symptom — already fixed in
  `TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-DEACTIVATE-RECOLOR-GAP`.
- `apply_plan.py:71`'s `invalidate_movement_cache` — already ruled out (see Request Summary).
- Any other consumer of `dirty_set` not identified in this investigation's initial scope; if one is
  found during investigation, document it here rather than silently expanding scope without a
  decision checkpoint.

## Acceptance Criteria
- [x] Real (not synthetic-only) test evidence exists for whether `phase_graph.py`'s phase
      short-circuiting actually skips a phase on a passive-decay-only tick, and whether that skip is
      observably consequential. Confirmed: skipped, but not consequential — see Implementation
      Notes / Consumer #1.
- [x] Real test evidence exists for whether the true read-model consumer (`ReadModelCache`, not
      `apply_plan.py`'s dead `invalidate_read_model` field — see Implementation Notes) actually
      leaves a stale read model for at least one tick following a passive-decay-only change.
      Confirmed: yes, real staleness.
- [x] A clear, evidenced verdict (confirmed bug / confirmed benign / inconclusive) is recorded for
      each of the two consumers in this ticket's Implementation Notes. Consumer #1: confirmed
      benign. Consumer #2: confirmed bug (at `ReadModelCache`, corrected from the ticket's own
      original naming of `apply_plan.py`'s dead field).
- [x] Consumer #2 is confirmed a real bug — a fix-approach decision was obtained via peer review
      (`rpg-feature-planning`) before any implementation began. **Decision**: a narrow fix scoped to
      `ReadModelCache` (supplementary post-apply dirty-id source from the already-computed
      `ApplyPlan.dirty_tags_by_entity`), not widening the shared `update.dirty_set` publication
      (unnecessary now that Consumer #1 is confirmed benign) — but explicitly conditioned on first
      weighing a second, materially different option the peer raised: wiring the dormant
      `BiologicalSystem.update()` (a real, unwired, explicit-`EntityUpdate`-producing decay
      implementation found during this investigation) in as the actual fix, which would eliminate
      this whole class of staleness at the source rather than patching the cache. Both options are
      recorded, with rationale, in the two follow-up tickets below — this investigation ticket
      itself implements neither, per its own Scope.
- [x] No further code change beyond what an investigation ticket may make in passing: corrected one
      stale comment (`src/domains/combat_engagement/phase.py:171`) that cited the dead
      `invalidate_read_model` field as if it were live — a real doc/code-comment parity fix found
      during this investigation, directly adjacent to its own scope.

## Related Tickets
- TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-DEACTIVATE-RECOLOR-GAP (sibling hotfix; origin of this
  finding; fixed the render-path symptom without touching this root gap)
- TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE (content change that exposed the render-path symptom,
  unrelated to this ticket's own scope)
- TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS (new, filed not implemented — the actual
  Consumer #2 fix, per the decision above)
- TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION (new, filed not implemented — the dormant
  "wire real EntityUpdates" alternative fix option, must be weighed before
  READMODEL-CACHE-PASSIVE-DECAY-STALENESS picks its final approach)

## Related Docs
- docs/engine/kernel.md (7-phase deterministic loop — relevant context for the phase-gating
  consumer)

## Related Stored Artifacts
None yet — standard tier, staging artifacts (`plan.md`, `investigation.md`, `test_plan.md`) to be
created under `staging_artifacts/TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION/` when
this ticket is picked up.

## Related Code Areas
- src/engine/pipeline.py (dirty_set publication, `AuthoritativeApplyPipeline.refine()`)
- src/engine/phase_graph.py (phase short-circuiting consumer)
- src/engine/apply_plan.py (read-model invalidation consumer; `ApplyPlanBuilder.build_plan()`'s
  passive-decay "candidates" path that produces the omitted changes in the first place)
- src/engine/apply.py (`ApplyPath._compute_entity_changes`, the apply()-local `dirty_builder` that
  currently only feeds audit validation)
- src/core/dirty.py (`DirtySetBuilder`, `DirtySet`)

## Assumptions / Open Questions
- Whether a real scenario exists where a tick's *only* dirty-domain-relevant change across the
  entire world is passive-decay-only (as opposed to always coinciding with at least one explicitly-
  updated entity in practice, which would make this benign in practice even though the mechanism is
  real) is exactly what this investigation needs to determine — not assumed either way.
- Whether `can_skip_when_no_dirty` is actually set on any phase whose `input_domains` includes
  `"lifecycle"` (or the other domains passive decay touches — `"biological"`) is not yet confirmed;
  if no such phase exists, the phase-short-circuiting consumer is benign by construction and that
  should be the recorded finding.

## Implementation Notes

Full investigation in
`staging_artifacts/TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION/investigation.md`.

**Consumer #1 (phase short-circuiting, `near_death_hardening`/`evolution`): CONFIRMED BENIGN.**
Both phases only ever iterate `update.entity_updates` — the exact same source
`DirtySetBuilder.mark_from_update()` reads to populate the dirty_set. A passive-decay-only entity
is invisible to both at once, by the same structural cause, so the tick-wide skip never discards
real pending work for either phase. Proved with a real `AuthoritativeApplyPipeline.refine()` run
plus running both phases directly (bypassing the skip) on the same input.

**Consumer #2: CONFIRMED BUG, at a different site than originally named.** The ticket's own
Request Summary named `apply_plan.py:72`'s `invalidate_read_model` field — re-grepped and confirmed
it is dead code, never read anywhere outside its own definition. The real, live consumer of this
gap is `ReadModelCache` (`src/api/read_model_cache.py`), wired every tick in
`V2EngineManager._update_latest_state()` off the same published `kernel.status.dirty_set`, backing
the real `get_entity`/`get_entities_paged` API endpoints. Its per-entity cache is only invalidated
for IDs in `dirty_set.all_dirty_entities` — a passive-decay-only entity's cached DTO is never
popped, so the API serves a stale snapshot indefinitely for whatever fields only changed via
passive decay.

Real, evidence-based scenario: an entity already dead in combat on a prior tick, whose only
remaining change is passive hunger accrual + `lifecycle.active` cleanup, with zero `EntityUpdate`
staged. An earlier scenario attempt (a *live* entity dying from passive decay for the first time)
was rejected — `strategic_intelligence`'s own always-on goal scoring
(`src/ai/goals/scorers.py`, `COMBAT_RETREAT`/`TOWN_RETURN` fallback) assigns *some* project to
essentially any live, cognitively active entity every tick regardless of HP, incidentally marking
it dirty via a different domain and masking the bug. This narrows, but does not eliminate, the
real blast radius: the bug reproduces for any entity that has already stopped acting (death, or
similarly excluded from strategic processing) whose passive attribute decay continues.

**Peer review (`rpg-feature-planning`) routing, per this ticket's own Scope**: proposed fix-approach
decision sent 2026-09-08 — since Consumer #1 turned out benign, recommend the ticket's own option
(b) (a narrow fix scoped to `ReadModelCache` specifically, e.g. a supplementary post-apply dirty-id
set sourced from the already-computed but currently apply()-local
`ApplyPlan.dirty_tags_by_entity`), not option (a) (widening the shared `update.dirty_set` itself,
which would also affect phase gating even though that's now confirmed unnecessary). Awaiting
peer concurrence before recording a final decision and closing.

Aside, not investigated further (out of this ticket's own scope, flagged for the fix-approach
discussion rather than dropped): `src/systems/biological_system.py`'s `BiologicalSystem.update()`
is a second, unwired, explicit-`EntityUpdate`-producing biological decay implementation — dead
code, referenced only by its own test. Possibly the dormant "make passive decay dirty-set-visible"
path that never got wired in; relevant context for whoever picks up the follow-up fix ticket.

## Test Summary
New file `tests/unit/engine/test_dirty_set_passive_decay_consumers.py` — 4 tests, all real
`AuthoritativeApplyPipeline.refine()`/`ApplyPath.apply_generation()`/`ReadModelCache` calls, no
mocking. All 4 pass. Scoped regression run (`pytest tests/unit/api/test_read_model_cache.py
tests/unit/domains/optimization/test_phase_dependency_graph.py tests/unit/engine/ -m "not slow and
not extra_slow"`, via `/home/u24desktop/Working/venv/bin/python3`) — 228 passed, 1 skipped, 3
deselected, 0 failed.

## Files Changed
- `tests/unit/engine/test_dirty_set_passive_decay_consumers.py` (new).
- `staging_artifacts/TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION/` (investigation.md,
  plan.md, test_plan.md — new).
- `src/domains/combat_engagement/phase.py` (one comment corrected — cited the dead
  `apply_plan.py` `invalidate_read_model` field as if live; now cites the real
  `ReadModelCache`/`dirty_set.all_dirty_entities` mechanism, with a pointer to this ticket).
- `tickets/todos/TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS.md` (new, filed not
  implemented — Consumer #2's actual fix).
- `tickets/todos/TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION.md` (new, filed not
  implemented — the alternative fix-option candidate raised during this investigation).

No other `src/` file changed — investigation-tier ticket; the confirmed fix for Consumer #2 lands
in its own follow-up ticket per the routed decision, not implemented here.

## Completion Summary
Investigated both named consumers of the published `dirty_set`'s omission of passive-decay-only
entity changes, with real pipeline/apply test evidence for each (not reasoning alone). Consumer #1
(phase short-circuiting, `near_death_hardening`/`evolution`): confirmed benign — both phases only
ever act on entities already present in `update.entity_updates`, the same source the dirty_set
itself is built from, so the skip structurally cannot discard real pending work. Consumer #2
(read-model invalidation): confirmed a real, live bug, but at a different site than this ticket's
own Request Summary originally named — `apply_plan.py`'s `invalidate_read_model` field is dead
code (confirmed by grep, corrected a stale comment that had assumed otherwise); the real consumer
is `ReadModelCache`, wired live in the API path, which serves stale entity data for entities whose
only per-tick change is passive decay, unbounded by any eviction (confirmed via a second grep that
`ReadModelCache` is never registered with `CacheRegistry`). A fix-approach decision was routed
through peer review before any implementation, per this ticket's own Scope and this repo's
decision-routing convention — resulting in two new, unimplemented follow-up tickets: the narrow
`ReadModelCache` fix, and a real, peer-escalated alternative (wiring a dormant, unwired
`BiologicalSystem.update()` implementation found during this investigation) that the fix ticket
must explicitly weigh before choosing its final approach, rather than defaulting past it.
