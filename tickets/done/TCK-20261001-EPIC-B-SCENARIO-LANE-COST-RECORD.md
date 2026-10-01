---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261001-EPIC-B-SCENARIO-LANE-COST-RECORD
phase: done
date: 2026-10-01
tags: [testing]
---

# TCK-20261001-EPIC-B-SCENARIO-LANE-COST-RECORD

## Title
Start the Epic B criterion 4 per-PR scenario-lane cost record

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Epic B criterion 4 asks for lane wall time on the first ~10 relevant PRs. The record had not started. Start it from the real CI runs of PRs #271 and #275, text only, in the same PR as the B1-B4 batch.

## Scope
- A per-PR table in Epic B: PR, head SHA, workflow run, the job that actually executed `tests/mechanic_scenarios`, conclusion, job wall time, why routed, test count.
- Every head SHA the job ran on, grouped per PR, re-checked through the Actions jobs API.
- State what the record is not: whole-job wall time, 2 of ~10, no trigger or docs-only case observed, not the "shared with feature teams" step.

## Out of Scope
- The curated-additions superset for baseline v2 (stays a later option).
- Promoting the scenario lane, sharing cost with feature teams, any workflow change.

## Acceptance Criteria
1. Table lists every head SHA with a workflow run for #271 and #275, with figures matching the jobs API.
2. Both PRs are marked tests-only fail-open; criterion 4 stays Open with 2 of ~10 stated.
3. Wall time is labelled whole-job; the not-yet-shared limit is stated.
4. Epic B file stays `phase: open` in tickets/todos/test-architecture/.

## Related Tickets
TCK-20261001-TEST-LANE-ROUTING-COST-VIEW-BASELINE-V2, TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION, TCK-20260930-TEST-DECISIONS-RECORD-AND-SCENARIO-LANE

## Related Docs
docs/plans/test_architecture/roadmap.md (§6, §11)

## Related Stored Artifacts
stored_artifacts/TCK-20261001-EPIC-B-SCENARIO-LANE-COST-RECORD/

## Related Code Areas
tickets/todos/test-architecture/

## Assumptions / Open Questions
- Route: hand-orchestrated. Requested through test-architecture-reviewer as the user's decision to add it to PR #275.
- Test counts were not retrieved (job JUnit not available); recorded as "not recorded", not 0.

## Implementation Notes
Runs and job times from `gh api .../actions/runs?head_sha=` and `.../runs/<id>/jobs`. #271 heads `a9646c9de` and `e75ff2e77` have no run. Routing counts re-derived by running `scenario_lane_paths` on each PR's file list.

## Test Summary
Text only. `tests/unit/tools` and `tests/docs` re-run after the edit; frontmatter validated.

## Files Changed
tickets/todos/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md; docs/REGISTRY.yaml.

## Completion Summary
Cost record started with three rows (#271 two heads, #275 one head): 51 s, 34 s, 48 s whole-job. Criterion 4 stays open.
