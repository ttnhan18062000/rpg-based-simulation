---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-ANCHORS
phase: open
date: 2026-06-30
tags: [simulation-quality, regression, testing, calibration]
---

# TCK-20260630-SIMQ-ANCHORS

## Title
Commit empirical grade regression anchors to test_grade_regression.py

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`tests/simulation_quality/test_grade_regression.py` currently contains placeholder
expectations from contract §11.3 that don't match empirical calibration data. Replace them
with confirmed grades from calibration runs. Add world-specific and long-run anchors once
TCK-20260630-SIMQ-CALFIX and TCK-20260630-SIMQ-ROUTING-TEST are complete.

## Scope
1. Update `test_grade_regression.py` with confirmed baseline grades (current data):

   | World | Seed | Ticks | COMBAT | NARRATIVE | PROGRESSION | Others |
   |---|---|---|---|---|---|---|
   | sandbox_world | 42 | 200 | B | A | C | C |
   | sandbox_world | 137 | 200 | B | A | C | C |
   | sandbox_world | 999 | 200 | B | A | B | C |

2. After TCK-20260630-SIMQ-CALFIX: add world-specific anchors for dungeon_crawl /
   urban_political / wilderness_survival (differentiated results)
3. After TCK-20260630-SIMQ-ROUTING-TEST: add anchors for simq_routing_test across all 10 pillars
4. After TCK-20260630-SIMQ-TIMEGATE: add long-run anchors (1000-tick grades)
5. Store anchor data as JSON fixture in `tests/simulation_quality/fixtures/grade_anchors.json`
6. Regression test: any pillar grade shift of >1 letter from anchor fails the test

## Out of Scope
- Changing grade thresholds or scoring weights
- Adding new pillars

## Acceptance Criteria
- [ ] `pytest tests/simulation_quality/test_grade_regression.py` passes with new anchors
- [ ] `tests/simulation_quality/fixtures/grade_anchors.json` committed with all confirmed baselines
- [ ] Grade matching uses band tolerance (1-letter): B anchor passes for B or A, fails for C
- [ ] At least sandbox_world (3 seeds × 200 ticks) anchors are present and passing
- [ ] Doc comment in test file explains update procedure (update fixture after intentional changes)

## Related Tickets
- TCK-20260630-SIMQ-CALFIX (world-differentiated anchors depend on this)
- TCK-20260630-SIMQ-ROUTING-TEST (10-pillar anchors depend on this)
- TCK-20260630-SIMQ-TIMEGATE (long-run anchors depend on this)

## Related Docs
- `docs/plans/simq_deep_audit_plan.md` §5 Track E
- `docs/simulation_quality/quality_scoring_contract.md` §11.3 (regression test spec)
- `data/calibration/` — calibration reports used as anchor source

## Related Stored Artifacts
- `data/calibration/sandbox_world_seed42_200t/quality_report.json`
- `data/calibration/sandbox_world_seed137_200t/quality_report.json`
- `data/calibration/sandbox_world_seed999_200t/quality_report.json`

## Related Code Areas
- `tests/simulation_quality/test_grade_regression.py`
- `tests/simulation_quality/fixtures/` (new: `grade_anchors.json`)

## Assumptions / Open Questions
- Band tolerance of ±1 letter is the current recommendation. If a pillar is anchor=B,
  accept {A, B, C} and fail on D or S. This prevents false negatives on natural variance
  while still catching regressions.
- Long-run anchor grades should be marked `@pytest.mark.slow` — they require running
  the engine for 1000 ticks.

## Implementation Notes
- Anchor format in `grade_anchors.json`:
  ```json
  {
    "sandbox_world_seed42_200t": {
      "COMBAT": "B", "NARRATIVE": "A", "PROGRESSION": "C",
      "AGENCY": "C", "COGNITION": "C", "ECONOMY": "C",
      "FACTION": "C", "INFORMATION": "C", "SOCIAL": "C", "WORLD": "C"
    }
  }
  ```
- Load fixture in test via `@pytest.fixture(scope="module")` reading the JSON file.
- Current test_grade_regression.py may have stale placeholder expectations — read it
  before writing new anchors.

## Test Summary
- Run `pytest tests/simulation_quality/test_grade_regression.py` to confirm anchors pass
- Verify that deliberately worsening a scorer causes the test to fail (mutation test)

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
