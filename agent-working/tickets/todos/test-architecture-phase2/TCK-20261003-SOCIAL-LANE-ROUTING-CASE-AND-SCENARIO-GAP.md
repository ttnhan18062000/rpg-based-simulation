---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-SOCIAL-LANE-ROUTING-CASE-AND-SCENARIO-GAP
phase: open
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-SOCIAL-LANE-ROUTING-CASE-AND-SCENARIO-GAP

## Title
Phase 2 social item 2 (Run): a lane routing case for `src/systems/social_systems/**`, and a scenario-gap record

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary

Phase 2 plan §6 item 2 (`docs/plans/test_architecture/phase2_social_scale_out.md`). `PERF_RE` in
`.github/workflows/test.yml` omits `src/systems/`, so a social-only `src/` change is not covered by
`Perf / cert / arena`. Pin the intended routing with one rule-level case, and record that no social
mechanic scenario exists. This is the **only test-file change in the whole Phase 2 batch**.

## Scope

1. Add one case to `tests/unit/tools/test_scenario_lane_paths.py`, in the existing routing-fixture
   block, in the style of `test_src_progression_only_routes_to_the_dedicated_job`: for
   `["src/systems/social_systems/appraisal.py"]`, `run is True` and `perf is False` (the dedicated
   `Scenario lane` job runs), against the live `PERF_RE` read from `test.yml`. The assertion is
   written against the measured behaviour and checked first by running the existing helper.
2. A scenario-gap record: state, with the full `origin/main` SHA and date, that `tests/mechanic_scenarios/`
   holds no social mechanic scenario (list what was searched). The record goes in the Phase 2 batch
   report's home (decided by C2/C3 reports' common doc, or `docs/testing/` if none yet) and is routed
   to `rpg-feature-planning`. Writing scenarios is out of scope.

## Out of Scope

- Any other test file. No `tests/unit/social/`, `tests/simulation_quality/`, `tests/integration/` or
  `tests/architecture/` file is edited, moved, marked, deleted or strengthened (owner constraint,
  2026-10-03).
- Changing `PERF_RE`, `scenario_lane_paths.py` or the workflow.
- Writing a social mechanic scenario.

## Acceptance Criteria

- [ ] `git diff --name-only` against `origin/main` shows exactly one test file,
  `tests/unit/tools/test_scenario_lane_paths.py`, plus the ticket, record, monitoring and registry files.
- [ ] The new case passes, reads `PERF_RE` from the workflow (no copied pattern), and fails if
  `src/systems/` were added to `PERF_RE` (positive control: checked once by temporarily reproducing
  that in a scratch copy, not in the tree).
- [ ] The scenario-gap record names what was searched, the SHA and the date, and states that the
  routing case is rule-level evidence, not a CI observation.
- [ ] The record carries the line: measurements of `relationships.py`, `appraisal.py` and
  `consequence_events.py` go stale when `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` lands.
- [ ] The existing file's tests all still pass.

## Related Tickets

- Parent: `TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL`.
- Pattern: `TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2` (done).

## Related Docs

- `docs/plans/test_architecture/phase2_social_scale_out.md` §6 item 2
- `docs/plans/test_architecture/roadmap.md` §6

## Related Stored Artifacts

None.

## Related Code Areas

- `tests/unit/tools/test_scenario_lane_paths.py`
- `tools/test_architecture/scenario_lane_paths.py`
- `.github/workflows/test.yml` (`PERF_RE`, read only)

## Assumptions / Open Questions

- Assumes `src/systems/social_systems/**` matches `TRIGGER_RE` (the `src/` prefix) and not `PERF_RE`;
  the case is written after measuring, and if the measurement differs the ticket stops and reports.
- Where the scenario-gap record lives is the reviewer's call at plan review.

## Implementation Notes

Figures re-measured at the then-current `origin/main` with the full SHA.

## Test Summary

Not run yet.

## Files Changed

None yet.

## Completion Summary

Not complete.
