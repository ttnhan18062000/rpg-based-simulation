---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-VARIANTS-METRIC
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, determinism, world]
---

# TCK-20260821-VISUAL-VARIANTS-METRIC

## Title
Variants validation metric: trail-activity liveliness and cross-spec TVD diversity

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promote the Variants metric — trail-activity liveliness plus cross-spec diversity via total-variation-distance (TVD) — into real production code.

## Scope
- Implement trail-activity = unique-tiles-visited / ticks-sampled, deciding a real entity-selection strategy to replace render_trail.py's current hardcoded "first entity in dict" choice
- Implement total_variation_distance(h1, h2) over terrain histograms, written fresh from PROPOSAL.md §5c (never saved to a file previously)
- Implement Variants as cross-*spec* comparison ONLY — no code path treats same-spec/different-seed as a diversity signal
- Both metrics computed as Tier-0, zero-image computations, reusing AuthoritativeState/DirtySet with no parallel tracking

## Out of Scope
- Multi-seed averaging / grade-band wiring (TCK-20260821-VISUAL-GRADE-SCORER's scope)
- Making the terrain-diversity half of multi-seed averaging meaningful — it stays a no-op until world-gen becomes seed-varied, which is unfiled/undecided (not this ticket)
- Threshold calibration (TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope)

## Acceptance Criteria
- [ ] Trail-activity is near-zero (~2-3 tiles/100+ ticks) for the confirmed-stuck entity pattern, and materially higher for a moving entity
- [ ] total_variation_distance(h1, h2) returns ~0.2315 for TVD(sandbox_world, dungeon_crawl) as a regression anchor
- [ ] total_variation_distance returns exactly 0.0 for same-spec-different-seed terrain histograms, matching the confirmed seed-invariant-terrain finding
- [ ] No code path in this module treats same-spec/different-seed as a diversity signal — only cross-spec comparisons are scored
- [ ] Both metrics run as Tier-0 zero-image computations with no image/render dependency

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/spatial_rendering/prototype/render_trail.py
- experiments/spatial_rendering/prototype/render_world.py
- experiments/spatial_rendering/PROPOSAL.md

## Assumptions / Open Questions
- render_trail.py's entity-selection strategy needs a real decision in this ticket (replacing the "first entity in dict" hardcode)
- Multi-seed averaging will be a no-op for the terrain-diversity half of this metric until world-gen becomes seed-varied — flagged separately, not decided in this batch
- simulation-quality tag: this metric is an architecturally-independent SimQ-sibling (not a PillarScorer/pillar), tagged for topical adjacency since it reuses SimQ's grade vocabulary rather than being part of the SimQ subsystem itself

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
