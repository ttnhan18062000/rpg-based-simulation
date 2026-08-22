---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP
phase: open
date: 2026-08-22
tags: [rendering, world]
---

# TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP

## Title
IncrementalRenderer.update() never repaints an entity from ENTITY_COLOR_ALIVE to ENTITY_COLOR_DEAD when it dies mid-run

## Status
OPEN

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
- [ ] An entity that dies in place (position unchanged, `combat.alive` flips to `False`) during an
      incremental render sequence is repainted `ENTITY_COLOR_DEAD` by the next `update()` call that
      processes it.
- [ ] A new regression test proves incremental-vs-full-render pixel identity for this exact
      in-place-death scenario.
- [ ] Existing `TCK-20260821-WORLD-RENDER-CORE` tests (`tests/unit/rendering/`) remain green,
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

## Test Summary

## Files Changed

## Completion Summary
