---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION
phase: open
date: 2026-09-08
tags: [determinism]
---

# TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION

## Title
Determine whether the published dirty_set's omission of passive-decay-only entity changes causes real phase-skip or read-model-staleness bugs

## Status
OPEN

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
- [ ] Real (not synthetic-only) test evidence exists for whether `phase_graph.py`'s phase
      short-circuiting actually skips a phase on a passive-decay-only tick, and whether that skip is
      observably consequential.
- [ ] Real test evidence exists for whether `apply_plan.py`'s read-model invalidation actually
      leaves a stale read model for at least one tick following a passive-decay-only change.
- [ ] A clear, evidenced verdict (confirmed bug / confirmed benign / inconclusive) is recorded for
      each of the two consumers in this ticket's Implementation Notes.
- [ ] If either consumer is confirmed a real bug, a fix-approach decision is obtained (per this
      repo's decision-routing convention) before any implementation begins, and that decision is
      recorded here with its rationale.
- [ ] If no consumer is confirmed a real bug, the ticket closes with that finding documented and no
      further code change — this is a legitimate, valuable outcome for an investigation ticket, not
      a failure to complete it.

## Related Tickets
- TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-DEACTIVATE-RECOLOR-GAP (sibling hotfix; origin of this
  finding; fixed the render-path symptom without touching this root gap)
- TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE (content change that exposed the render-path symptom,
  unrelated to this ticket's own scope)

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
_(pending — this ticket is filed, not yet picked up for investigation)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
