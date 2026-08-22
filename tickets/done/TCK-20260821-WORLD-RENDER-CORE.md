---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-WORLD-RENDER-CORE
phase: open
date: 2026-08-21
tags: [rendering, determinism, world]
---

# TCK-20260821-WORLD-RENDER-CORE

## Title
Deterministic batch/QA world renderer for AuthoritativeState

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a canonical, deterministic way to render a world (AuthoritativeState) to a PNG image, with DirtySet-incremental caching, storage under data/runs/{run_id}/renders/ reusing the existing RetentionPolicy, and a golden-hash regression test proving bit-identical output across independent runs (SHA256, 3 independent runs). This is the load-bearing prerequisite every other visual-quality ticket in this batch (C2-C9) depends on.

## Scope
- Implement render(state, out_path) producing a valid PNG from AuthoritativeState geometry, in a new src/ module (module placement, e.g. src/rendering/ vs src/world/rendering/, must be decided as part of this ticket)
- Implement DirtySet-incremental rendering that reuses src/core/dirty.py's existing DirtySet tracking, not a parallel dirty-tracking mechanism
- Store render output under data/runs/{run_id}/renders/, reusing src/observability/reporting/retention.py's RetentionPolicy unmodified
- Normalize terrain-string casing ('PLAIN'/'plain'/'forest') at the render boundary with a loud fallback for unrecognized values, as a workaround only
- Golden-hash regression test: 3 independent renders of the same state produce bit-identical SHA256
- Regression test proving DirtySet-incremental render output is pixel-identical to a full re-render

## Out of Scope
- Fixing the underlying terrain-string casing inconsistency at its source
- Deciding/implementing the historical-tick rendering interval
- Adding numpy or any new third-party dependency — pure-stdlib must meet the zero-new-dependency bar
- Any of the metric/scoring/calibration/agent-review work covered by sibling tickets in this batch

## Acceptance Criteria
- [x] render(state, out_path) produces a valid PNG file for a given AuthoritativeState
- [x] Three independent renders of the same state produce bit-identical SHA256 hashes (golden-hash regression test)
- [x] DirtySet-incremental render produces pixel-identical output to a full re-render of the same state
- [x] Render output written under data/runs/{run_id}/renders/ is correctly aged/pruned by the existing RetentionPolicy with zero changes made to retention.py — satisfied as the honest, code-verified behavior documented in Implementation Notes (renders/ persists across normal per-file expiry, is removed only when the whole run directory is purged via the genuine evaluation-error path), not the AC's more literal "individually aged" phrasing, which the real unmodified retention.py cannot do. Flag for Verify: if a reviewer insists on the literal wording, that's a ticket-reword decision, not a retention.py edit.
- [x] No new third-party dependency (e.g. numpy) is added to satisfy this ticket's rendering path
- [x] Terrain-string casing variants ('PLAIN'/'plain'/'forest') are normalized at the render boundary with a loud fallback for unrecognized values, not silently mismapped

## Related Tickets
- TCK-20260820-EPIC-WORLD-RENDERING-CORE
- TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP (follow-up, filed 2026-08-22, for the
  mid-run-death recoloring gap disclosed in Completion Summary/Implementation Notes)

## Related Docs
- docs/engine/contracts/regression_and_verification.md

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/spatial_rendering/prototype/png_writer.py
- experiments/spatial_rendering/prototype/render_world.py
- experiments/spatial_rendering/prototype/render_incremental.py
- experiments/spatial_rendering/prototype/render_numpy.py
- experiments/spatial_rendering/prototype/benchmark.py
- experiments/spatial_rendering/prototype/render_trail.py
- experiments/spatial_rendering/prototype/render_annotated.py
- src/core/state.py
- src/core/dirty.py
- src/engine/kernel.py
- src/engine/legality.py
- src/observability/reporting/retention.py

## Assumptions / Open Questions
- Module placement (e.g. src/rendering/ vs src/world/rendering/) is not specified anywhere yet and must be decided by this ticket
- Historical-tick rendering interval is undecided and left open for a future ticket
- numpy is deliberately excluded as a new dependency; pure-stdlib is assumed sufficient

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260821-WORLD-RENDER-CORE/plan.md`'s 10 steps, promoting
the three `experiments/spatial_rendering/prototype/` scripts into a new top-level `src/rendering/`
package (`png_writer.py`, `render.py`, `incremental.py`), pure stdlib (`struct`/`zlib` only).

- `src/rendering/png_writer.py`: `write_png()` promoted verbatim.
- `src/rendering/render.py`: `TERRAIN_COLORS`, `DEFAULT_TERRAIN_COLOR`, `terrain_color()`,
  `BUILDING_COLOR`/`ENTITY_COLOR_ALIVE`/`ENTITY_COLOR_DEAD`/`BLOCKED_OUTLINE`, the new `DRAW_ORDER`
  constant (terrain → buildings → blocked_outline → entities), `render(state, out_path, scale=6)`,
  and the new `render_output_path(base_dir, run_id, filename)` storage helper
  (`{base_dir}/{run_id}/renders/{filename}`, does not route through
  `RunArtifactRepository.resolve_path`).
- `src/rendering/incremental.py`: `IncrementalRenderer` and the new
  `dirty_entity_ids_for_render(kernel_status, all_entity_ids)` helper (falls back to the full
  entity-id set when `kernel_status.dirty_set` is absent, matching `src/core/dirty.py`'s own
  fallback convention; otherwise returns `ds.movement_entities | ds.lifecycle_entities`).

**Deviation from strict verbatim promotion (see plan.md's Deviations section for full detail):**
Step 3 called for a verbatim promotion of `IncrementalRenderer`, but that alone could not satisfy
AC #3 against any real compiled world — confirmed empirically against `sandbox_world` (seed 42).
Two additions were required and made:
1. `__init__`'s static-background construction now also paints `BUILDING_COLOR`/`BLOCKED_OUTLINE`
   (previously terrain-only), since `blocked_tiles` is non-empty in every real world checked and
   is static for a run's lifetime (no `DirtySet` domain tracks it) — it belongs in the I-frame
   cache, not a per-tick concern.
2. `__init__` now seeds every currently-alive-and-active entity's position onto `self.frame` /
   `self.last_entity_pos` at construction — without this, entities that never become
   movement/lifecycle-dirty (≈9 of 18 in `sandbox_world` over 20 ticks) would never be drawn at
   all, unlike `render()`'s unconditional per-entity draw.

Verified after this fix: `sha256(incremental_final.png) == sha256(full_final.png)` for
`sandbox_world`/seed 42 over 15 ticks. Known remaining gap, not fixed (documented, out of scope):
`update()` never paints `ENTITY_COLOR_DEAD` for an entity that dies mid-run — not exercised by
this ticket's test scenario (zero deaths confirmed empirically), flagged for a follow-up ticket.

**AC #4 / retention.py**: zero edits made to `retention.py`, as required. Investigation.md's Risk
#1 description of the corrupted-run purge trigger was subtly inaccurate — confirmed by direct
execution that the "missing manifest" branch's `reason` string never actually satisfies
`execute_cleanup()`'s purge condition (a real, pre-existing `reason`-string/`files`-list mismatch
in `retention.py` itself, not introduced by this ticket), so that branch never removes a run
directory today; only a genuine evaluation exception does. Test file
(`tests/unit/rendering/test_render_retention_integration.py`) was written against this verified
real behavior — 3 tests instead of 2: normal-expiry-leaves-renders-untouched,
full-purge-on-genuine-evaluation-error, and an explicit documentation test pinning the
missing-manifest run's surprising survival today.

**Step 10 (docs)**: only `docs/engine/contracts/regression_and_verification.md` was updated (§1
Captured Artifacts item 4, §4 Determinism Check render-specific paragraph). Per explicit
instruction from the dispatching orchestrator, `docs/parity_ledger/infrastructure.yaml`'s new
entry is deferred to this pipeline's separate Parity phase, not written here.

## Test Summary

All new tests pass; all regression-surface commands from
`staging_artifacts/TCK-20260821-WORLD-RENDER-CORE/test_plan.md` pass unmodified.

```
PYTHONPATH=. pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v
  -> 10 passed

PYTHONPATH=. pytest tests/unit/observability/test_retention_manager.py tests/unit/observability/reporting/test_phase27_behavior_artifact_paths.py -v
  -> 5 passed (all pre-existing, unmodified)

PYTHONPATH=. pytest tests/perf/test_dirty_parity.py tests/perf/test_dirty_set_integrity.py -v -m "not slow"
  -> 4 passed, 1 deselected (pre-existing, unmodified)

PYTHONPATH=. pytest tests/unit/worldbuilding/ -v
  -> 133 passed (pre-existing, unmodified — compiler.py untouched)

PYTHONPATH=. pytest tests/docs/test_doc_integrity.py -q
  -> 10 passed, 1 skipped
```

`git status` confirms zero diffs to any Scope-Guarded file (`retention.py`,
`artifact_repository.py`, `dirty.py`, `compiler.py`, `kernel.py`, `legality.py`).

## Files Changed

- `src/rendering/__init__.py` (new, empty)
- `src/rendering/png_writer.py` (new)
- `src/rendering/render.py` (new)
- `src/rendering/incremental.py` (new)
- `tests/unit/rendering/__init__.py` (new, empty)
- `tests/unit/rendering/test_render_core.py` (new)
- `tests/unit/rendering/test_terrain_color_normalization.py` (new)
- `tests/unit/rendering/test_render_incremental.py` (new)
- `tests/unit/rendering/test_render_storage_integration.py` (new)
- `tests/unit/rendering/test_render_retention_integration.py` (new)
- `tests/architecture/test_rendering_zero_new_dependency_guard.py` (new)
- `docs/engine/contracts/regression_and_verification.md` (edited — new render artifact
  subsection under §1, render-specific determinism paragraph under §4)
- `staging_artifacts/TCK-20260821-WORLD-RENDER-CORE/plan.md` (edited — added Deviations section)
- `tickets/inprogress/TCK-20260821-WORLD-RENDER-CORE.md` (this file — edited)

## Completion Summary

Implemented a deterministic, pure-stdlib batch/QA world renderer as a new top-level
`src/rendering/` package: `render(state, out_path)` for full-frame PNG output,
`IncrementalRenderer`/`dirty_entity_ids_for_render` for DirtySet-filtered incremental rendering
reusing `src/core/dirty.py`'s real DirtySet, and `render_output_path()` for
`data/runs/{run_id}/renders/` storage path construction. All 6 acceptance criteria are met and
covered by 10 new passing tests (golden-hash determinism, PNG validity, no-state-mutation,
DirtySet-incremental pixel-identity to a full re-render, terrain-casing normalization with loud
fallback, zero-new-dependency architecture guard, storage-path integration, and honest
retention.py-behavior documentation for AC #4). Two necessary corrections beyond the plan's
literal "verbatim promotion" instruction were required and are fully documented in
Implementation Notes and plan.md's Deviations section: completing `IncrementalRenderer`'s static
I-frame (buildings/blocked-tile overlay, initial entity seeding) so DirtySet-incremental output
is genuinely pixel-identical to `render()` against a real compiled world, and correcting the
retention-test design around a real, pre-existing `retention.py` quirk (missing-manifest runs are
flagged eligible but never actually purged today). Zero edits to any of the six scope-guarded
files; zero new third-party dependencies (enforced by a permanent architecture-guard test).
`docs/parity_ledger/infrastructure.yaml`'s new entry (`INFRA-369`) was added in this pipeline's
Parity phase.

**One known, deliberately-deferred gap, tracked with a real follow-up ticket (not left as
unlinked prose):** `IncrementalRenderer.update()` never repaints an entity from
`ENTITY_COLOR_ALIVE` to `ENTITY_COLOR_DEAD` when it dies in place (no position change, so it never
enters the `movement_entities | lifecycle_entities` dirty-id union) — a real pixel-divergence risk
this ticket's own `test_dirty_set_incremental_render_pixel_identical_to_full_rerender` does not
exercise (its scenario has zero mid-run deaths). Filed as
`TCK-20260822-HOTFIX-INCREMENTAL-DEATH-RECOLOR-GAP` in the same `world-rendering-core` batch
folder.
