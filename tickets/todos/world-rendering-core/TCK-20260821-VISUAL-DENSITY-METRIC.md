---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-DENSITY-METRIC
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, world]
---

# TCK-20260821-VISUAL-DENSITY-METRIC

## Title
Density validation metric: nearest-neighbor CV and terrain histogram

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promote the Density metric — entity nearest-neighbor coefficient of variation plus terrain-type histogram — into real production code.

## Scope
- Implement nearest-neighbor coefficient-of-variation (CV) function over entity positions, written from the documented one-off verification numbers (sandbox_world≈0.648, dungeon_crawl≈0.678) since no prototype file exists
- Implement terrain-type histogram computation, reusing/extracting the terrain_histogram side effect already committed in render_world.py rather than reimplementing it
- Both metrics computed as a Tier-0 pure-data path, zero image required
- Treat clustering CV as a non-monotonic, healthy-band signal (not "more is better"/dormancy-style single-direction rule) at the raw-metric level

## Out of Scope
- Multi-seed calibration of healthy-band thresholds (TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope)
- Switching to Kernel.get_world_indexes/entities_by_tile for O(N) scaling — current O(N^2) is acceptable at today's entity counts (11-32); flag only, do not implement
- Any grade-band/scoring combination logic (TCK-20260821-VISUAL-GRADE-SCORER's scope)

## Acceptance Criteria
- [ ] Nearest-neighbor CV function reproduces sandbox_world≈0.648 and dungeon_crawl≈0.678 within a stated tolerance
- [ ] Terrain histogram dict values sum exactly to len(state.terrain)
- [ ] Both metrics are computed via a Tier-0 pure-data path with zero image/render dependency
- [ ] No PillarScorer subclass is created and no SimQ event-pipeline import exists in this module

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/engine/kernel.py
- src/core/dirty.py
- experiments/spatial_rendering/prototype/render_world.py
- src/simulation_quality/pillars.py

## Assumptions / Open Questions
- Nearest-neighbor CV was never committed to a prototype file; the AC tolerance for reproducing sandbox_world/dungeon_crawl numbers must be finalized during implementation
- Entity counts stay low enough (11-32) that O(N^2) is acceptable for now; Kernel.get_world_indexes is flagged, not adopted, in this ticket
- simulation-quality: this metric is an architecturally-independent SimQ-sibling (not a PillarScorer/pillar), tagged for topical adjacency since it reuses SimQ's grade vocabulary rather than being part of the SimQ subsystem itself

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
