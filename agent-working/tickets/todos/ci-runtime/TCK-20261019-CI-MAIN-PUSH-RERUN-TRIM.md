---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-MAIN-PUSH-RERUN-TRIM
phase: open
date: 2026-10-19
tags: [testing, workflows, performance]
---

# TCK-20261019-CI-MAIN-PUSH-RERUN-TRIM

## Title
Main pushes keep the full test suite. Only work that is informational or wasted on a main push is moved off it, and only after platform-planner and lead-planner (ubuntu) confirm nothing they read depends on it.

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Child 3 of TCK-20261019-CI-RUNTIME-EPIC. Measured over 7 days: 70 main pushes, about 58 runner-hours of test.yml (31%). The informational `simq-grade-drift` job runs about 10 min on every main push. Cancelled runs (a newer push superseding an older run) cost about 12 h.

**Hard constraint (lead-planner-u24, 2026-10-19):** a main push is the squash of a PR that was tested against an older base. The full run on main is the only check that catches two green PRs that conflict once both are merged, and several PRs merge a day. This ticket must not skip test lanes on main by changed files.

## Scope
1. **Consult first, before any change, and record the answers in investigation.md:**
   - **platform-planner (u24):** does anything of theirs read main-push test.yml runs or artifacts? Candidates: publish-images gating, deploy-docs and the DevOps alerts.
   - **lead-planner (ubuntu):** do the Slow regression watchdog, the perf baselines or the rpg gate report read main-push artifacts or statuses, including the SimQ drift output?
   - No change goes ahead while either is unanswered. If either says yes for an item, that item stays.
2. **Candidate changes**, each conditional on step 1:
   - (a) Run `simq-grade-drift` on schedule and `workflow_dispatch` only, not on push. It is informational, and its scheduled run keeps the signal.
   - (b) Measure the cancelled-run waste on main by `concurrency` group. If main pushes cancel each other mid-run, the newest push still runs the full suite, so this is acceptable. Record the measurement; change nothing unless the waste is in non-main refs and a fix keeps every PR's final run.
3. Write up the options that would reduce the full suite on main, for the owner to decide. None is implemented here:
   - a nightly full run plus changed-files skipping on push;
   - a GitHub merge queue.
   For each, state the safety it gives up and the hours it saves, from the epic's baseline. lead-planner takes it to the owner.

## Out of Scope
- Skipping any test lane on a main push by changed files.
- Enabling a merge queue or changing branch protection (owner and platform).
- Other workflows.

## Acceptance Criteria
- [ ] AC1: investigation.md records platform-planner's and lead-planner (ubuntu)'s answers, quoted with dates, before any workflow change.
- [ ] AC2: every lane except `simq-grade-drift` still runs on every main push. Show this with a static test over test.yml's `if:` conditions that fails if a non-informational job gains a push-skip.
- [ ] AC3: if (a) is done, the first scheduled run after merge shows `simq-grade-drift` running and producing its usual summary. Quote the run id.
- [ ] AC4: the owner write-up exists in investigation.md and was sent to lead-planner-u24.
- [ ] AC5: **lead-planner-u24 AND lead-planner (ubuntu) review the PR by comment**, in addition to testing-planner, before the user merges. Record both links.

## Related Tickets
- TCK-20261019-CI-RUNTIME-EPIC (parent)
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS (the changed-files gate)
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (why simq drift runs where it does; read it before moving it)

## Related Docs
- docs/guides/delivery_process.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261019-CI-RUNTIME-EPIC/investigation.md (baseline)

## Related Code Areas
- .github/workflows/test.yml (`on:`, `concurrency:`, `simq-grade-drift`)
- tests/static/ (the new push-lane guard)

## Assumptions / Open Questions
- If TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED shows the drift job was put on push on purpose, to catch a red on main within one merge, then (a) needs testing-planner's ruling. Do not decide it yourself.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
