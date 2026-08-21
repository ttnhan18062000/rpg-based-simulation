---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-SHAPE-METRIC
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, world]
---

# TCK-20260821-VISUAL-SHAPE-METRIC

## Title
Shape validation metric: connected-component fill-ratio and rotation detection

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promote the Shape metric — connected-component-aware fill-ratio plus rotation/repetition detection — into real production code, motivated by a real corpus finding that 78.8% of measured biome components across 18 worlds score >=0.95 fill-ratio (near-perfectly rectangular), including one exact case of a 90-degree-rotated duplicate component pair.

## Scope
- Implement connected_components() over AuthoritativeState.terrain, written fresh from experiments/spatial_rendering/PROPOSAL.md's inline algorithm/prose since no prototype file exists to promote
- Implement per-component fill-ratio scoring
- Implement rotation/repetition detection between components
- Pure visualization/geometry computation only — zero data-lookup checks
- Document the known fill-ratio weakness (composite of unioned rectangles scoring artificially low/organic) as a stated limitation in code/docstrings, not solved in this ticket

## Out of Scope
- Calibrating or tuning the 0.95 threshold (separate ticket, TCK-20260821-VISUAL-QUALITY-CALIBRATION)
- Subclassing PillarScorer or integrating with SimQ's event pipeline — this is an architecturally independent sibling, not a pillar
- Any grade-band/scoring combination logic (TCK-20260821-VISUAL-GRADE-SCORER's scope)

## Acceptance Criteria
- [ ] connected_components() run on the dungeon_crawl world's AuthoritativeState.terrain reproduces the documented result of FOREST being 2 components of 1,116 tiles each, not 1
- [ ] Per-component fill-ratio reproduces the documented values: CAVE=0.980, FOREST-c0=1.000, FOREST-c1=1.000, RUIN=1.000
- [ ] Rotation detection reproduces the documented 90-degree-rotation finding between the two FOREST components
- [ ] A corpus-wide run across all 18 worlds reproduces 26/33 components scoring >=0.95, with every sub-0.95 component being FOREST type
- [ ] No PillarScorer subclass is created and no ObservabilityEventEnvelope/QualityHub import exists in this module

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/spatial_rendering/PROPOSAL.md
- src/core/state.py
- src/simulation_quality/scorers/base.py
- src/simulation_quality/pillars.py
- config/simulation_quality/grade_thresholds.yaml

## Assumptions / Open Questions
- The 0.95 fill-ratio threshold is uncalibrated and provisional until the calibration ticket runs
- No prototype script exists for this logic despite the 'promote' framing — it must be written fresh from PROPOSAL.md
- simulation-quality: this metric is an architecturally-independent SimQ-sibling (not a PillarScorer/pillar), tagged for topical adjacency since it reuses SimQ's grade vocabulary and mirrors its precedent rather than being part of the SimQ subsystem itself

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
