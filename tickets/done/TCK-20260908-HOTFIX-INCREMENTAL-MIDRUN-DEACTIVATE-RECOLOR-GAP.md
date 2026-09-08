---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-DEACTIVATE-RECOLOR-GAP
phase: done
date: 2026-09-08
tags: [rendering, world]
---

# TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-DEACTIVATE-RECOLOR-GAP

## Title
IncrementalRenderer leaves a stale ENTITY_COLOR_DEAD pixel when an entity deactivates purely via passive decay, invisible to the tick's published dirty_set

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/unit/rendering/test_render_incremental.py::test_dirty_set_incremental_render_pixel_identical_to_full_rerender`
fails deterministically on `sandbox_world` (seed 42, 15 ticks) — first observed as a CI blocker on
PR #148 after `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` added `wolf_den_nest` content, which
shifted this exact seed/tick trajectory enough to newly exercise a real, pre-existing gap (not a
defect in the new content itself — confirmed via direct before/after content swap).

Root-caused via direct instrumentation of a real compiled `Kernel` run (not guesswork — two prior
theories were raised and directly falsified first: a Place-dirty-tracking gap, and a bounds/canvas
mismatch between `render()` and `IncrementalRenderer.__init__` — both disproven by reproduction,
see Implementation Notes):

1. Entity id=19 (`orc_warrior`) dies in real combat at tick 5. It has an explicit `EntityUpdate`
   that tick (position + combat change), so `dirty_entity_ids_for_render()` correctly includes it;
   `IncrementalRenderer.update()` correctly paints `ENTITY_COLOR_DEAD` at its cell.
2. At tick 6, `entity.lifecycle.active` flips `True` -> `False` via `ApplyPath._compute_entity_changes`'s
   passive-decay branch (`src/engine/apply.py:109`, `active=(new_hp > 0 and new_age < life.max_age_ticks)`).
   This computation runs entirely inside `ApplyPlanBuilder.build_plan`'s "candidates" passive-decay
   fallback (`src/engine/apply_plan.py:299-314`) for entities with **no** explicit `EntityUpdate`
   submitted that tick (a dead entity stops acting).
3. The published `dirty_set` — the one field both `Kernel._run_hard_law_checks`/`kernel._status.dirty_set`
   and `dirty_entity_ids_for_render()` read — is finalized by `AuthoritativeApplyPipeline.refine()`
   (`src/engine/pipeline.py:56-58`, `DirtySetBuilder(update.dirty_set)` / `mark_from_update`)
   **before** `ApplyPath.apply()`/`ApplyPlanBuilder` ever runs. It only sees `update.entity_updates`.
4. `ApplyPlanBuilder`'s own per-entity tag computation for this passive change
   (`plan.dirty_tags_by_entity`, `src/engine/apply_plan.py:363`) does get consumed
   (`src/engine/apply.py:264-265`, `dirty_builder.mark_entity(e_id, tags)`) — but into a **separate,
   apply()-local** `DirtySetBuilder()` instance (`src/engine/apply.py:234`) used only for audit
   validation against the pre-existing dirty_set (`src/engine/apply.py:496-497`). It never updates
   the actual published `update.dirty_set`.

Net effect: the real state correctly deactivates at tick 6 (`render()` correctly skips inactive
entities, `src/rendering/render.py:78`), but `dirty_entity_ids_for_render()` never returns eid=19
for tick 6 (or any later tick), so `IncrementalRenderer.update()` is never called for it again — the
stale `ENTITY_COLOR_DEAD` pixel painted at tick 5 is never restored to terrain. Verified via direct
trace: `19 in dirty_entity_ids_for_render(...)` is `True` at tick 5, `False` at tick 6, even though
the persisted `active` flip demonstrably happens at that exact tick boundary.

This is a real, general, pre-existing bug (not introduced by the M2 content batch): any entity that
dies and later deactivates purely via passive decay, with no other explicit action that tick, will
leave a stale corpse-colored pixel under `IncrementalRenderer`. It is a distinct bug class from
`TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP` (which covered an entity already-dead at
renderer *construction* time) — this is the mid-run counterpart, same shape of fix.

**This ticket is renderer-local only.** The deeper question — whether the same "published dirty_set
under-reports passive-decay-only changes" gap causes real misbehavior in the two other consumers
that read `update.dirty_set` (`src/engine/phase_graph.py`'s phase short-circuiting and
`src/engine/apply_plan.py`'s read-model-invalidation gating) — is explicitly out of scope here and
tracked separately as `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION` (standard tier,
P2, investigation-first, since merging the apply()-local `dirty_builder` into the published
`dirty_set` would change what `dirty_set` means for every consumer at once, including phase gating —
a determinism-relevant change that deserves its own Verify pass, not a side effect of a render fix).

## Scope
- `IncrementalRenderer.update()` (`src/rendering/incremental.py`) additionally reconciles every
  entity id it is currently tracking in `last_entity_pos` whose `lifecycle.active` has gone `False`
  since it was last drawn, restoring that cell's background — even when that id is absent from the
  tick's `dirty_entity_ids` argument. This is a dict scan over already-tracked ids (bounded by how
  many entities the renderer has ever drawn), not a new full-state scan, so it carries no meaningful
  per-tick cost beyond the existing `update()` call.
- Regression test: reproduce the exact `sandbox_world` mid-run-deactivation scenario (or a synthetic
  equivalent, matching the existing `test_incremental_render_repaints_entity_that_dies_in_place`
  pattern) proving incremental-vs-full-render pixel identity across the tick where an entity goes
  from dead-but-active to fully inactive with no explicit `EntityUpdate` that tick.
- Confirm `test_dirty_set_incremental_render_pixel_identical_to_full_rerender` passes with the fix.

## Out of Scope
- Any change to `src/core/dirty.py`, `src/engine/pipeline.py`, or `src/engine/apply.py`'s dirty-set
  publication — this ticket does not touch the dirty-set/apply boundary at all, by design (see
  Request Summary). That question belongs to
  `TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION`.
- Any other `IncrementalRenderer` gap not related to this specific mid-run-deactivation scenario.

## Acceptance Criteria
- [x] An entity that deactivates (`lifecycle.active` True->False) purely via passive decay, with no
      explicit `EntityUpdate` that tick, is restored to background by `IncrementalRenderer` no later
      than the next `update()` call, even though it is absent from that tick's `dirty_entity_ids`.
- [x] A new regression test proves incremental-vs-full-render pixel identity for this exact scenario.
- [x] `test_dirty_set_incremental_render_pixel_identical_to_full_rerender` passes.
- [x] `tests/unit/rendering/` full suite remains green.

## Related Tickets
- TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP (prior fix, same bug class, construction-time
  case)
- TCK-20260821-WORLD-RENDER-CORE (origin of the pixel-identity contract this protects)
- TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE (content change that newly exposed this pre-existing
  gap)
- TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION (the deeper, non-render question this
  ticket deliberately does not answer)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent.

## Related Code Areas
- src/rendering/incremental.py
- tests/unit/rendering/test_render_incremental.py

## Assumptions / Open Questions
None — root cause fully confirmed via direct instrumentation before this ticket was filed (see
Request Summary and Implementation Notes).

## Implementation Notes

**Investigation history (both prior theories directly falsified before the real root cause was
found):**
1. Initial hypothesis (Place-dirty-tracking gap in `dirty_entity_ids_for_render()`) — not
   investigated further once a more specific mechanism was found.
2. Peer-reviewed hypothesis (bounds/canvas-dimension mismatch between `render()`'s terrain+entity
   bounds computation and `IncrementalRenderer.__init__`'s terrain-only bounds) — directly falsified
   by reproduction: both renderers compute identical 212x200 bounds/canvas dimensions for this exact
   scenario (first reproduction attempt had an accidental scale mismatch giving a misleading
   result; corrected and reran with matching `scale=2` on both sides).
3. Real root cause found via a raw pixel-buffer diff (monkeypatching `write_png` in both
   `src.rendering.incremental` and `src.rendering.render` to capture pixel data directly, since PIL
   is not installed in this environment) narrowing the divergence to exactly 4 pixels (one 2x2 grid
   cell at grid coord (84, 49)): incremental shows `(96, 48, 48)` = `ENTITY_COLOR_DEAD`, full render
   shows `(42, 42, 58)` = `SWAMP` terrain. Then confirmed via direct instrumentation of
   `ApplyPath._compute_entity_changes` and `dirty_entity_ids_for_render()` across a real 15-tick run
   — see Request Summary for the full mechanism.

Peer review (`rpg-feature-planning`) additionally identified two other consumers of the same
published `dirty_set` that could theoretically be affected by the same passive-decay-omission gap
(`src/engine/phase_graph.py` phase short-circuiting, `src/engine/apply_plan.py` read-model
invalidation gating) — both independently verified against real code. A third candidate the peer
initially raised (`src/engine/apply_plan.py:71`'s `invalidate_movement_cache`) was checked and ruled
out: it reads only `update.dirty_set is not None`, never the set's contents, so an under-reported
set cannot affect it. Per that review, this ticket stays scoped to the renderer-local fix only; the
2-consumer investigation question is tracked separately (see Out of Scope and Related Tickets).

**Fix applied**, entirely inside `IncrementalRenderer.update()` (`src/rendering/incremental.py`):
after the existing per-dirty-id loop, a second pass scans `self.last_entity_pos` (bounded by
distinct ids the renderer has ever drawn, not a full-state scan) for any tracked id absent from
`dirty_entity_ids` whose current `state.entities.get(eid).lifecycle.active` is `False` (or whose
entity has vanished from `state.entities` entirely) — restores that cell's background and stops
tracking it. This reconciliation runs regardless of dirty-set membership, so an entity that
deactivates purely via apply-time passive decay is fixed within the very next `update()` call
instead of never being revisited.

**Regression test** (`tests/unit/rendering/test_render_incremental.py`,
`test_incremental_render_restores_background_when_entity_deactivates_off_dirty_set`): builds the
same real compiled-world `Kernel` + `IncrementalRenderer` harness as the two existing tests in this
file, ticks 5 times to reach a live baseline, then constructs a synthetic state via
`dataclasses.replace` that flips one already-tracked, currently-active entity's `lifecycle.active`
to `False` — and calls `renderer.update(died_state, set())`, deliberately passing an **empty**
`dirty_entity_ids` to reproduce the exact real-world gap (a passive-decay-only deactivation never
appears in the published dirty_set). Asserts the entity is dropped from `last_entity_pos` and that
the incremental frame's PNG hash matches a full `render()` of the same post-deactivation state.
Confirmed the test fails without the fix (reverted `src/rendering/incremental.py` alone via a
temporary stash, reran — both this new test and the pre-existing
`test_dirty_set_incremental_render_pixel_identical_to_full_rerender` failed) and both pass with the
fix restored, before finalizing.

## Test Summary
`python3 -m pytest tests/unit/rendering/test_render_incremental.py -v` — 3 passed (including the new
regression test; the pre-existing `test_dirty_set_incremental_render_pixel_identical_to_full_rerender`
now passes against real `sandbox_world`, no scenario change needed).
`python3 -m pytest tests/unit/rendering/ -v` — 95 passed, 0 failed. All pre-existing tests in this
directory (`TCK-20260821-WORLD-RENDER-CORE`, `TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP`,
and the visual-review/shape/variants/density/grading suites) remain green and unmodified in their
own assertions.
Verified the new test is a genuine regression guard by temporarily reverting
`src/rendering/incremental.py` alone (via `git stash`, then re-applied and dropped) and confirming
both it and the original CI-blocking test fail pre-fix, then pass post-fix.

## Files Changed
- `src/rendering/incremental.py` — `IncrementalRenderer.update()` now reconciles tracked entities
  that have gone inactive even when absent from `dirty_entity_ids`.
- `tests/unit/rendering/test_render_incremental.py` — new regression test
  `test_incremental_render_restores_background_when_entity_deactivates_off_dirty_set`.
- `tickets/inprogress/TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-DEACTIVATE-RECOLOR-GAP.md` — this
  ticket.

## Completion Summary
Fixed a real, pre-existing, general bug: `IncrementalRenderer` never learned about an entity's
deactivation when that deactivation came purely from `ApplyPath`'s apply-time-only passive-decay
pass (no explicit `EntityUpdate` that tick), because the published `dirty_set` — read by both the
Kernel's hard-law-check status and the render dirty-id helper — is finalized in
`AuthoritativeApplyPipeline.refine()` before `ApplyPath.apply()` ever runs. This left a stale
alive/dead-colored pixel on the map wherever such an entity last stood. The fix reconciles tracked
entities directly against their live `lifecycle.active` state on every `update()` call, independent
of dirty-set membership — restoring pixel identity with a full re-render without touching the
dirty-set/apply boundary itself. Root cause was found via direct instrumentation of a real
`sandbox_world` run after two prior theories (Place-dirty-tracking gap; a bounds/canvas mismatch
proposed by peer review) were each directly falsified by reproduction. The peer review that
falsified the second theory also surfaced two other consumers of the same published `dirty_set`
that may or may not be affected by the same underlying omission — that broader question is
deliberately out of scope here and tracked as its own standard-tier investigation ticket,
`TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION`, so as not to bundle an
architecturally-sensitive dirty-set-publication change into what should be a narrow, low-risk
render fix.
