---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-CONNECTIVITY-METRIC
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, world]
---

# TCK-20260821-VISUAL-CONNECTIVITY-METRIC

## Title
Connectivity validation metric: whole-map walkable-region reachability

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promote the Connectivity metric — whole-map walkable-region reachability via BFS — into real production code.

## Scope
- Implement a BFS connectivity function over AuthoritativeState.terrain/blocked_tiles, reusing LegalityServiceV2.verify_occupancy's exact walkability rule (terrain != "WALL" minus blocked_tiles) rather than re-deriving it
- Return raw structural facts (walkable tile count, connected-component count) plus a derived percent-reachable value, not just a boolean
- Pure geometry computation, no data-lookup checks
- New tests covering both a fully-connected case and a constructed >=2-disconnected-island fixture

## Out of Scope
- Grade-band/scoring integration (TCK-20260821-VISUAL-GRADE-SCORER's scope)
- CI-gating this metric — report-only, never CI-gated
- Expanding evidence beyond dungeon_crawl to other worlds (single-world/single-seed evidence is accepted here; broader multi-world coverage is TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope)

## Acceptance Criteria
- [ ] BFS connectivity function using exactly LegalityServiceV2.verify_occupancy's walkability rule reproduces the documented dungeon_crawl result: 15,245 walkable tiles, 1 connected component, 100% reachable
- [ ] Function returns raw structural facts (walkable count, component count) plus derived percent-reachable, not just a pass/fail boolean
- [ ] New test covers a fully-connected map case
- [ ] New test covers a constructed map with >=2 disconnected islands
- [ ] Tests live under tests/unit/, with no tests/parity/ marker applied

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/legality.py
- src/core/state.py
- src/simulation_quality/pillars.py
- experiments/spatial_rendering/PROPOSAL.md

## Assumptions / Open Questions
- Evidence base is currently single-world/single-seed (dungeon_crawl only); broader coverage is deferred to the calibration ticket
- The dependency on the renderer ticket is structural/sequencing per epic ordering — the metric itself only needs AuthoritativeState.terrain/blocked_tiles, not actual rendered pixels
- simulation-quality tag: this metric is an architecturally-independent SimQ-sibling (not a PillarScorer/pillar), tagged for topical adjacency since it reuses SimQ's grade vocabulary rather than being part of the SimQ subsystem itself

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
