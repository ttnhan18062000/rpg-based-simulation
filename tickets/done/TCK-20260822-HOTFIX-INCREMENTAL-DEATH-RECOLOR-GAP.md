---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP
phase: done
date: 2026-08-22
tags: [rendering, world]
---

# TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP

## Title
IncrementalRenderer.update() never repaints an entity from ENTITY_COLOR_ALIVE to ENTITY_COLOR_DEAD when it dies mid-run

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`src/rendering/incremental.py`'s `IncrementalRenderer.update(state, dirty_entity_ids)` restores an
entity's old cell then re-blits it using its *current* `alive`/`active` status when the entity is
present in `dirty_entity_ids` — but an entity's death alone does not add it to the
`movement_entities | lifecycle_entities` union `dirty_entity_ids_for_render()` computes, unless the
entity also moved or its `active` flag flipped in the same tick. Concretely: an entity that dies in
place (no position change, `combat.alive` flips `False` but `lifecycle.active` stays `True`, e.g. a
corpse left on the map) is never re-blitted, so it stays rendered in `ENTITY_COLOR_ALIVE` even
though a full non-incremental `render()` call against the same state would correctly draw it in
`ENTITY_COLOR_DEAD`. This is a real pixel-divergence between the incremental and full-render paths
for that specific scenario.

Found as a byproduct of implementing `TCK-20260821-WORLD-RENDER-CORE` (the batch's prerequisite
renderer ticket) — that ticket's own `test_dirty_set_incremental_render_pixel_identical_to_full_rerender`
test scenario has zero mid-run deaths, so it does not exercise this gap and correctly stays green.
Documented, not fixed, in that ticket's Implementation Notes and `plan.md`'s Deviations section,
per its own explicit scope guard against building a parallel diffing mechanism without evidence a
real gap exists — this ticket is that evidence.

## Scope
- Extend `dirty_entity_ids_for_render()` (or the caller's dirty-id computation) in
  `src/rendering/incremental.py` to also include entities whose `combat.alive` flag changed since
  the last captured frame, not just `movement_entities | lifecycle_entities`.
- Add a regression test: tick a synthetic entity to death in place (no position change) across an
  incremental-vs-full-render comparison, assert pixel identity — the direct regression guard this
  gap needs, mirroring `TCK-20260821-WORLD-RENDER-CORE`'s existing
  `test_dirty_set_incremental_render_pixel_identical_to_full_rerender` pattern but specifically
  covering the in-place-death case that test's own scenario does not exercise.

## Out of Scope
- Any other IncrementalRenderer gap not related to death-state recoloring.
- Changes to `src/core/dirty.py` itself — this ticket only changes how `src/rendering/incremental.py`
  consumes `DirtySet`'s existing fields (or, if no existing field tracks alive-state transitions,
  documents that as a real follow-on finding rather than inventing a new `DirtySet` domain, since
  extending `DirtySet` itself is a bigger architectural decision than this hotfix's scope).

## Acceptance Criteria
- [x] An entity that dies in place (position unchanged, `combat.alive` flips to `False`) during an
      incremental render sequence is repainted `ENTITY_COLOR_DEAD` by the next `update()` call that
      processes it.
- [x] A new regression test proves incremental-vs-full-render pixel identity for this exact
      in-place-death scenario.
- [x] Existing `TCK-20260821-WORLD-RENDER-CORE` tests (`tests/unit/rendering/`) remain green,
      unmodified in their own assertions.

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE (origin of this finding)
- TCK-20260820-EPIC-WORLD-RENDERING-CORE (parent epic)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent.

## Related Code Areas
- src/rendering/incremental.py
- src/core/dirty.py (read-only context — DirtySet's existing fields, if any, that could carry this signal)

## Assumptions / Open Questions
- Whether `DirtySet` already has a field that would carry this signal (e.g. a combat/lifecycle
  transition domain) or whether the fix needs to track alive-state itself inside
  `IncrementalRenderer` (comparing previous vs. current `combat.alive` per dirty-or-candidate
  entity) is not yet investigated — left for this ticket's own hotfix-tier implementation to
  determine directly against the real `DirtySet` fields.

## Implementation Notes

**Investigation finding (resolves the Assumptions/Open Questions item above) — the ticket's own
diagnosis of the root cause was wrong, the real bug is elsewhere:**

`DirtySet` already carries the alive-transition signal, and `dirty_entity_ids_for_render()`
already includes it. Traced empirically (not just read): every code path that flips
`combat.alive` — `src/engine/combat.py`'s engagement resolution and `src/engine/world_dynamics.py`'s
hazard-death path — does so exclusively by attaching a `CombatUpdate(alive_set=...)` onto
`EntityUpdate.combat` (`src/core/updates.py`); `CombatPatch.apply()` (`src/engine/patches.py:292-310`)
is the *only* place `combat.alive` is ever written, and it always reads that value off
`u_com.alive_set` from the same `CombatUpdate`. Consequently `DirtySetBuilder.mark_from_update`/
`DirtySet.from_update` always mark the dying entity into `combat_entities` (`if e_upd.combat: ...`),
and `DirtyDependencyGraph.expand()`'s existing "combat implies lifecycle" rule
(`if combat: lifecycle.update(combat)`, `src/core/dirty.py`) then propagates it into
`lifecycle_entities` on every `DirtySetBuilder.build()`/`DirtySet.from_update()` call — including the
pipeline's final one (`src/engine/pipeline.py:352-353`) that becomes `kernel._status.dirty_set`.
Verified directly: ran `AuthoritativeApplyPipeline.refine()` against a synthetic in-place-kill
`StateUpdate` (no `new_position`, only `CombatUpdate(alive_set=False)`) on a real compiled world
state and confirmed `eid in refined.dirty_set.lifecycle_entities` is `True`. So
`dirty_entity_ids_for_render()`'s existing `ds.movement_entities | ds.lifecycle_entities` union
(`src/rendering/incremental.py`) **already** includes an entity that died in place, every tick.
Scope item 1 as literally written ("extend `dirty_entity_ids_for_render()`... to also include
entities whose `combat.alive` changed") was therefore not implemented — there is nothing to add,
and adding a redundant union arm would be a no-op that obscures this finding. `src/core/dirty.py`
was not touched, consistent with Out of Scope.

**The real, verified bug:** `IncrementalRenderer` (`src/rendering/incremental.py`) never referenced
`ENTITY_COLOR_DEAD` at all — only `ENTITY_COLOR_ALIVE`. In both `__init__`'s initial full-frame seed
and `update()`'s per-dirty-entity draw, the per-entity branch was gated on
`getattr(ent.lifecycle, "active", True) and ent.combat.alive`: a dead-but-active entity fell into the
`else`/no-draw path, which restores the background cell and (in `update()`) pops the entity from
`last_entity_pos` — so a corpse silently reverts to plain terrain instead of `ENTITY_COLOR_DEAD`,
diverging pixel-for-pixel from `render()` (`src/rendering/render.py:133-136`), which unconditionally
draws `ENTITY_COLOR_ALIVE if alive else ENTITY_COLOR_DEAD` for every active entity.

**Fix applied**, entirely inside `IncrementalRenderer`:
- Imported `ENTITY_COLOR_DEAD` from `src/rendering/render.py` (matching the file's existing pattern
  of importing shared color/terrain constants from `render.py` rather than re-declaring them).
- `__init__`'s entity-seeding loop and `update()`'s per-entity draw both now gate solely on
  `lifecycle.active` and pick `ENTITY_COLOR_ALIVE if ent.combat.alive else ENTITY_COLOR_DEAD` —
  mirroring `render()`'s own branch exactly. Both paths also now track `last_entity_pos` for
  dead-but-active entities (previously only alive ones were tracked), so a later tick that redraws
  that cell for any other reason still has a valid old position to restore first.
- Updated the stale `__init__` comment ("seed every currently-alive entity's position") to state
  the corrected alive-or-dead-active seeding behavior.

**Regression test** (`tests/unit/rendering/test_render_incremental.py`,
`test_incremental_render_repaints_entity_that_dies_in_place`): builds the same real compiled-world
`Kernel` + `IncrementalRenderer` harness as the existing
`test_dirty_set_incremental_render_pixel_identical_to_full_rerender`, ticks it 5 times to reach a
live baseline, then constructs a synthetic post-death `AuthoritativeState` via
`dataclasses.replace` (flips one currently-alive entity's `combat.alive` to `False`, asserts
position and `lifecycle.active` are unchanged — this is the exact in-place-death precondition),
calls `renderer.update(died_state, {eid})`, and asserts the incremental frame's PNG hash equals a
full `render()` of the same `died_state`. Confirmed the test fails without the fix (reverted
`src/rendering/incremental.py` only, reran — assertion failed with mismatched hashes) and passes
with it, before finalizing.

## Test Summary
`python3 -m pytest tests/unit/rendering/test_render_incremental.py -v` — 2 passed (including the new
regression test).
`python3 -m pytest tests/unit/rendering/ -v` — 94 passed, 0 failed. All pre-existing
`TCK-20260821-WORLD-RENDER-CORE` tests remain green and unmodified in their own assertions.
Verified the new test is a genuine regression guard by reverting `src/rendering/incremental.py`
alone and confirming it fails (hash mismatch) before the fix, then passes after.

## Files Changed
- `src/rendering/incremental.py` — import `ENTITY_COLOR_DEAD`; fix `__init__` and `update()` to draw
  dead-but-active entities `ENTITY_COLOR_DEAD` instead of silently reverting to background; comment
  update.
- `tests/unit/rendering/test_render_incremental.py` — new regression test
  `test_incremental_render_repaints_entity_that_dies_in_place`; added `dataclasses` import.
- `tickets/inprogress/TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP.md` — this ticket (Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).

## Completion Summary
Fixed the real bug: `IncrementalRenderer` never drew `ENTITY_COLOR_DEAD` for a dead-but-active
entity (corpse), in either its initial frame seed or its per-tick dirty-entity update — it only
ever drew `ENTITY_COLOR_ALIVE` or silently reverted the cell to background. Investigation
disproved the ticket's own stated root cause: `DirtySet`'s existing "combat implies lifecycle"
derived-dirtiness rule already propagates every `combat.alive` transition into
`lifecycle_entities`, so `dirty_entity_ids_for_render()`'s current `movement_entities |
lifecycle_entities` union was already correct and needed no change (verified empirically against
the real pipeline, not just read). The fix — mirroring `render()`'s own
alive/dead color branch inside `IncrementalRenderer.__init__` and `.update()` — is now
pixel-identical to a full re-render for an in-place death, covered by a new regression test that
was confirmed to fail pre-fix and pass post-fix, alongside the full green
`tests/unit/rendering/` suite (94 passed).
