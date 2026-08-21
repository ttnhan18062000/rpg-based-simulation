---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-CALIBRATION
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, calibration, world]
---

# TCK-20260821-VISUAL-QUALITY-CALIBRATION

## Title
Multi-seed/multi-world threshold calibration for the visual-quality metric families

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Calibrate healthy-band thresholds for all four metric families (Shape, Density, Variants, Connectivity) across multiple seeds/worlds, mirroring tools/calibrate_simq.py's real precedent — none of the four families have calibrated thresholds yet.

## Scope
- Write a calibration script mirroring calibrate_simq.py's CLI/output shape, running each of the 4 metric families across >=3 seeds
- Write a quality_report-equivalent artifact per (world, seed)
- Write healthy-band values to a config file with a provenance header (date, ticket ID, worlds, seeds, ticks) matching grade_thresholds.yaml's exact header format
- Mirror calibrate_simq.py's CalibrationIntegrityError-style run-integrity guard
- Explicitly record Shape's zero cross-seed terrain variance as expected behavior, not a bug, in the calibration output
- Expand Density/Variants/Connectivity evidence from their current 1-3-world coverage to comparable multi-world coverage

## Out of Scope
- CI-gating these thresholds — no pytest/CI gate may consume them
- Resolving whether FOREST needs its own separate threshold band (open question, flagged not resolved)
- Any change to the metric/scoring implementations from the other tickets in this batch

## Acceptance Criteria
- [ ] A calibration script mirroring calibrate_simq.py's CLI/output shape runs each of the 4 metric families across >=3 seeds and writes a quality_report-equivalent artifact per (world, seed)
- [ ] Healthy-band values are written to a config file with a provenance header (date, ticket ID, worlds, seeds, ticks) matching grade_thresholds.yaml's exact header format
- [ ] Output explicitly records Shape's zero cross-seed variance as expected, not flagged as a bug
- [ ] No pytest/CI gate consumes these thresholds
- [ ] A run-integrity guard mirroring CalibrationIntegrityError (queue-drop/corruption hard-fail) is present in the calibration script

## Related Tickets
- TCK-20260821-VISUAL-GRADE-SCORER
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/calibrate_simq.py
- config/simulation_quality/grade_thresholds.yaml
- experiments/spatial_rendering/prototype/render_world.py
- experiments/spatial_rendering/prototype/render_trail.py
- experiments/spatial_rendering/prototype/render_annotated.py

## Assumptions / Open Questions
- Evidence base is uneven across the four families: Shape already has 18-world/33-component single-seed coverage, while Density/Variants/Connectivity have only 1-3 worlds each
- Whether FOREST needs its own separate threshold band is an open question, not resolved by this ticket

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
