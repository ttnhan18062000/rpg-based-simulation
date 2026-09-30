---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-TEST-DECISIONS-RECORD-AND-SCENARIO-LANE
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-TEST-DECISIONS-RECORD-AND-SCENARIO-LANE

## Title
Record the D-R2, D-MF and D-M2 decisions, correct the pilot, baseline and report records, and add the non-required CI scenario-lane job

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
The owner approved D-R2, D-MF and D-M2 with changes. Record them, lift the HOLD markers without making any epic read as complete, correct the verified overclaims in the pilot report, baseline doc and core-RPG report, and implement the D-R2 scenario lane as a dedicated job that is not a merge gate.

## Scope
- Roadmap §11 and related text, INDEX.md, Epics B, C and D: record decisions, remove HOLD markers, correct status wording.
- `regression_policy.md`: bounded quarantine (§6.1), precedence line, oracle rule (§13.5). `architecture_design_notes.md` §7.3 additions.
- Pilot report and baseline doc corrections (what ran where, mutation-survivor scope, escaped-defect 0 wording, key rename note).
- `core_rpg_report.py`: state `not-run` becomes `not-in-supplied-runs` for a file absent from supplied runs; manifest key `worktree_dirty` becomes `scanned_inputs_dirty`; schema_version 2; `impact_report.py` consistency.
- New `tools/test_architecture/scenario_lane_paths.py` (fail-open path classifier) and a `scenario-lane` job in `.github/workflows/test.yml`, deduplicated against `perf-cert-arena`, with per-run wall time in the job summary.
- create-tickets epic template seeds the test-plan fixtures subsection (pending agent-working-design conflict check).

## Out of Scope
- Product code or behaviour changes. Quarantine tooling; nothing is quarantined.
- Making the scenario-lane job required (`main` has no branch protection; "non-required" is by convention). Changing `PERF_RE`.
- Wiring the oracle-review step into an agent file (Epic C part 5 wiring stays open).
- The `done-checker` test-plan field check (agent-working-design owns it as an advisory WARN).
- The real-pipeline exercise (a separate step; needs rpg-feature-planning's ticket and the user's go-ahead).
- Rewriting stored pilot or baseline artifacts (they keep `worktree_dirty` and `not-run` as historical files).

## Acceptance Criteria
- [x] No HOLD marker remains for D-R2, D-MF, D-M2; Epics B, C, D read as open with the corrected statuses; the epics stay in tickets/todos/.
- [x] Policy text and the oracle rule are recorded as specified; no test is quarantined.
- [x] Pilot report separates local, CI and pipeline; baseline doc wording corrected.
- [x] Report state and manifest key renamed with tests; schema_version bumped; consumers updated.
- [x] Scenario-lane classifier is unit-tested and fails open; the job runs the lane exactly once per PR.
- [x] Every trigger and irrelevant path list entry has evidence in investigation.md; anything unevidenced fails open.

## Related Tickets
- TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION, TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING, TCK-20260929-EPIC-CORE-RPG-TEST-PILOT

## Related Docs
- docs/plans/test_architecture/roadmap.md
- docs/testing/regression_policy.md
- docs/testing/core_rpg_test_pilot_2026-09-30.md, docs/testing/core_rpg_test_baseline_2026-09-30.md

## Related Stored Artifacts
None.

## Related Code Areas
tools/test_architecture/; .github/workflows/test.yml; docs/testing/; tickets/todos/test-architecture/

## Assumptions / Open Questions
- Known-irrelevant and trigger lists derive from an audit-hook run of tests/mechanic_scenarios (investigation.md); a new dependency path fails open.

## Implementation Notes
Impact report: `executed: not-run` meant "no supplied evidence", so it now reads `no-junit-artifact` (no run) or `not-in-supplied-runs` (run lacks the file). The mutation layer's own `{"state":"not-run"}` stays: it means the layer was not run.

## Test Summary
Scoped run: `pytest tests/unit/tools tests/tools/test_create_tickets_epic_fixtures_seed.py tests/tools/test_ci_workflow_test_coverage.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_workflow_vocabulary_check.py tests/tools/test_workflow_runtime_acorn_parse.py`: 533 passed, 2 skipped, 1 xfailed. New: `test_scenario_lane_paths.py` (routing, fail-open on empty diff and error, workflow-shape single-run condition), three report tests (schema_version 2, `not-in-supplied-runs` vs `no-junit-artifact`, caveat text), create-tickets seed test. Audit-hook run of `tests/mechanic_scenarios`: 53 passed. **The new `scenario-lane` job and the changed-files outputs have not yet run in CI** (they run on this PR).

## Files Changed
`.github/workflows/test.yml`, `.claude/workflows/create-tickets.js`, `tools/test_architecture/{scenario_lane_paths,core_rpg_report,impact_report}.py`, tests under `tests/unit/tools/` and `tests/tools/`, `docs/testing/{regression_policy,test_taxonomy,core_rpg_test_pilot_2026-09-30,core_rpg_test_baseline_2026-09-30}.md`, `docs/plans/test_architecture/{roadmap.md,reference/architecture_design_notes.md}`, `tickets/todos/test-architecture/*`.

## Completion Summary
Decisions D-R2, D-MF, D-M2 recorded; HOLDs lifted with Epics B, C, D still open (B part 2 in progress, C criteria 1-2 not met and 4 open and 5 met text-only, D open). Pilot, baseline and report overclaims corrected; report state and manifest key renamed (schema_version 2). Non-required scenario-lane job added, deduplicated against perf-cert-arena. Not done: oracle-review agent wiring, done-checker field check (agent-working-design, advisory WARN), quarantine tooling, real-pipeline exercise.
