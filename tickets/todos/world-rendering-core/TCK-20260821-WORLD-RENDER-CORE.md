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
OPEN

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
- [ ] render(state, out_path) produces a valid PNG file for a given AuthoritativeState
- [ ] Three independent renders of the same state produce bit-identical SHA256 hashes (golden-hash regression test)
- [ ] DirtySet-incremental render produces pixel-identical output to a full re-render of the same state
- [ ] Render output written under data/runs/{run_id}/renders/ is correctly aged/pruned by the existing RetentionPolicy with zero changes made to retention.py
- [ ] No new third-party dependency (e.g. numpy) is added to satisfy this ticket's rendering path
- [ ] Terrain-string casing variants ('PLAIN'/'plain'/'forest') are normalized at the render boundary with a loud fallback for unrecognized values, not silently mismapped

## Related Tickets
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

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

## Test Summary

## Files Changed

## Completion Summary
