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
- `min_events` is `PILLAR_MIN_EVENTS: Mapping[PillarId, int]` in `src/simulation_quality/pillars.py`, beside `PillarId` and away from the weights (rpg-planner, 2026-10-14); default 3 for every pillar.
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
The min_events table's home is ruled (pillars.py, PILLAR_MIN_EVENTS); the consumer audit is in Implementation Notes.

## Implementation Notes
Plan only; build held for testing's harness ticket TCK-20261013-SIMQ-NO-DATA-PILLAR-IN-GRADE-REGRESSION, which lands with it, and the single re-anchor follows both and (a).

Consumer audit (read 2026-10-14; what each does on a null grade or score):
- `src/simulation_quality/quality_report.py` `PillarSnapshot` (grade: str, normalized_score: float) and `QualityReportBuilder.build`: the producer; gains `status`, `min_events`, `reason`, nullable grade/score; the overall weighted sum skips no-data pillars (existing aggregation over status-ok ones), counts `pillars_scored`/`pillars_no_data`, and is no-data below half scored.
- `src/simulation_quality/api/routes.py:68,115,143`: reads `snap.normalized_score` and `snap.grade` into JSON responses: nulls pass through as JSON null; add `status` to each pillar object.
- `tools/calibrate_simq.py:586`: `print(f"... grade={snap.grade} norm={snap.normalized_score:+.4f}")` CRASHES on None (a format spec on None): print `no-data (n events < k)` for a no-data pillar.
- `src/simulation_quality/persistence.py:64-65` writes quality_report.json: serialises the new fields (nulls as null); `src/api/server.py:85-91` calls the same writer: no change.
- `tools/evaluate_simq.py:85`: reads quality_report.json per run key (the proof driver's rows): its pillar/overall values feed testing's `simq_reanchor`: testing's.
- `run_health.py` and the run_health sidecar: independent of grades: no change.
- `tools/calibrate_rendering.py:150`: writes its own quality_report-equivalent JSON for the rendering calibration: not the simulation_quality report: no change.
- Anything under `tools/test_architecture/` (the grade-regression harness and `simq_reanchor`) is testing's and covered by their harness ticket; so are the tests that read grades from the report (they would crash on nulls or read them as C).

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
