---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-GRADE-SCORER
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, world]
---

# TCK-20260821-VISUAL-GRADE-SCORER

## Title
Sibling grade-band scoring system for visual-quality metrics

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a grade-band scorer reusing SimQ's exact S/A/B/C/D/F thresholds, architecturally independent from SimQ, computing directly from AuthoritativeState geometry via the Shape/Density/Variants/Connectivity metric outputs. Structured as hard rules (binary facts), soft rules (gradient signals with a healthy band, non-monotonic), and scoring rules combining them into a grade. Multi-seed averaging across a world spec's renders is core to this system's design — currently a no-op since terrain is seed-invariant, but built now so it activates once world-gen becomes seed-varied.

## Scope
- Design and implement the currently-unspecified hard+soft -> single-normalized-score combination step needed before grade assignment (the real design risk identified in investigation)
- Implement grade assignment reusing the exact threshold table (S:2.0, A:0.5, B:0.0, C:-0.5, D:-1.0), sourced from a config file, never hardcoded in scorer code
- Implement non-monotonic soft-rule scoring: a healthy-band soft rule produces a positive delta inside its range and a negative delta at BOTH low and high extremes
- Implement multi-seed averaging: given N per-seed scores for one world spec, the averaged score = arithmetic mean; with N=1 it equals that single score exactly
- Decide module/config file location and naming
- Confirm layer should be 'world' (not 'engine'), matching epic/idea-doc precedent

## Out of Scope
- Registering a new PillarId, subclassing PillarScorer, or importing ObservabilityEventEnvelope/QualityHub/PillarAccumulator/ScoringContext
- Multi-seed/multi-world threshold calibration itself (TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope — this ticket builds the averaging mechanism, not the calibrated values)
- CI-gating — report-only, never CI-gated
- Data-lookup or placement-legality checks

## Acceptance Criteria
- [ ] Grade assignment returns the correct letter per the exact reused threshold table (S:2.0, A:0.5, B:0.0, C:-0.5, D:-1.0), sourced from a config file, not hardcoded
- [ ] A soft rule with a healthy band produces a positive delta inside its range and a negative delta at BOTH low and high extremes (non-monotonic, tested explicitly, unlike SimQ's linear cascade)
- [ ] Given N per-seed scores for one world spec, the averaged score equals the arithmetic mean; with N=1 it equals that single score exactly (the documented current no-op case)
- [ ] The module does not import ObservabilityEventEnvelope, QualityHub, PillarAccumulator, or ScoringContext, and does not register a new PillarId
- [ ] This ticket explicitly confirms (not assumes) whether the sibling system needs a parity-ledger entry or is exempt like SimQ's own grading system

## Related Tickets
- TCK-20260821-VISUAL-SHAPE-METRIC
- TCK-20260821-VISUAL-DENSITY-METRIC
- TCK-20260821-VISUAL-VARIANTS-METRIC
- TCK-20260821-VISUAL-CONNECTIVITY-METRIC
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/simulation_quality/quality_report.py
- src/simulation_quality/pillars.py
- config/simulation_quality/grade_thresholds.yaml
- tools/calibrate_simq.py
- src/core/state.py

## Assumptions / Open Questions
- The hard+soft -> single-normalized-score combination step is unspecified upstream and must be designed within this ticket
- No parity-ledger entry exists for SimQ's own grading system; this ticket confirms rather than assumes whether the sibling system is similarly exempt
- Tests/AC assert the N=1 identity/no-op case only — a variance-reduction case is out of scope since seed-varied world-gen is unfiled
- simulation-quality tag: this system is an architecturally-independent SimQ-sibling (not a pillar/subsystem member) — tagged for topical adjacency since it deliberately reuses SimQ's grade vocabulary/thresholds rather than being part of the SimQ subsystem itself

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
