---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261014-PILLARS-REPORT-NO-DATA-BELOW-A-MINIMUM-EVENT-COUNT
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-PILLARS-REPORT-NO-DATA-BELOW-A-MINIMUM-EVENT-COUNT

## Title
Below a minimum event count a pillar reports no-data in the quality report, not the plateau-penalty constant (PROGRESSION -8/51 = -0.1569).

## Status
OPEN (planned; build HELD until testing's harness ticket is ready, because the current tests crash on nulls or read them as C and the two land together)

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
With no XP in 200 ticks the only PROGRESSION event is the plateau penalty (weight -8, fires at tick 51), so the report gives C/-8/51 = -0.15686 for every such run, in any world; 23 of the 81 committed anchors already pin it. The scorer cannot tell "nothing happened" from "bad". Contract agreed by rpg-planner and testing-planner (2026-10-14).

## Scope
`quality_report.json`, EVERY pillar always present:
`{"status": "ok"|"no-data", "grade": <GRADE_ORDER letter>|null, "normalized_score": <float>|null, "event_count": n, "min_events": k, "reason": "below_min_events"}`
- `reason` appears only on no-data. On no-data, grade and score are null: never a placeholder number, never an invented grade string.
- `min_events` is a named, typed per-pillar table in the scoring contract module (`src/simulation_quality/`, symbol to be named at build; default 3 for every pillar).
- Overall is computed only over status-ok pillars with the existing aggregation, and emits `pillars_scored` and `pillars_no_data` beside it. With fewer than half the pillars scored, overall is `{"status": "no-data", "grade": null, "normalized_score": null, "reason": "too_few_pillars_scored"}`.
- Anchors are testing's: `simq_reanchor` writes `{"status": "no-data", ...}`; `grade_anchors.json` is not touched here.

## Out of Scope
Re-anchoring (testing); the INFORMATION transition fix (TCK-20261014-INFORMATION-DIVERGENCE-EVENT-FIRES-ON-ENTERING-THE-DIVERGED-STATE-NOT-EVERY-UPDATE).

## Acceptance Criteria
- A pillar with fewer than min_events events reports no-data with null grade and score and `reason`; at or above it reports ok as today.
- Overall excludes no-data pillars, reports the two counts, and is no-data below half the pillars scored.
- Every pillar key is present in every report; two runs of the same seed write the same bytes.
- Consumers of quality_report.json (the hub, tools/calibrate_simq.py, tests reading grades) handle nulls, landing together with testing's harness ticket.

## Related Tickets
TCK-20261014-POST-536-PROGRESSION-FLOOR-AND-INFORMATION-SPIKE-IN-200T-GRADE-ANCHORS; TCK-20261014-INFORMATION-DIVERGENCE-EVENT-FIRES-ON-ENTERING-THE-DIVERGED-STATE-NOT-EVERY-UPDATE.

## Related Docs
docs/simulation_quality/

## Related Stored Artifacts
None yet.

## Related Code Areas
src/simulation_quality/quality_report.py (QualityReportBuilder.build, PillarSnapshot), the scoring contract module (weights.py or its neighbour), tools/calibrate_simq.py.

## Assumptions / Open Questions
Which module holds the typed min_events table (weights.py, pillars.py or a new contract module) is chosen at build and reported to rpg-planner; consumers to audit before build: grep for normalized_score and "grade" readers.

## Implementation Notes
Plan only.

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
