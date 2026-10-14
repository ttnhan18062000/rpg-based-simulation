---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-ACTIONS-MAJORS-COMBINED
phase: open
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-ACTIONS-MAJORS-COMBINED

## Title
Land the GitHub Actions majors (#572-#575) as one verified PR, with testing-planner's artifact proof

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The owner chose to take the Actions majors now. They touch workflows owned by others (test.yml and slow-regression.yml by testing; rpg-gate-report.yml, deploy-docs.yml, pr-body-lint.yml, slow-regression-watchdog.yml). testing-planner requires download-artifact (#572) and upload-artifact (#575) to land **together**, with artifact proof rather than green status.

## Scope
- One branch that combines the changes of #572 (download-artifact 4→8), #573 (checkout 4→7), #574 (upload-pages-artifact 3→5)
  and #575 (upload-artifact 4→7). Keep the existing tag-pin style of those workflows (no SHA re-pinning; that is a separate
  owners' decision).
- Evidence from testing-planner, all of it in the PR body:
  1. One `workflow_dispatch` run of rpg-gate-report.yml on this branch whose report lists the per-world docs (not empty or
     no-data rows).
  2. The PR run's artifact list shows test.yml's 3 artifacts (incl. `perf-tripwire`) and slow-regression's 2, each with
     their files present (check hidden/dotfile paths and `if-no-files-found`).
  3. The `perf-tripwire` artifact shows both arms measured (second checkout into `perf-base`, #573).
- deploy-docs (#574): note that it runs only on main, so it can't be proven on the PR. State that plainly and have the owner
  watch the first main run.
- Request review by comment from testing-planner, plus the owners of the other touched workflows.

## Out of Scope
Changing workflow logic. SHA-pinning those workflows. Merging (user). Closing #572-#575 (user, after this lands).

## Acceptance Criteria
- Evidence items 1-3 are in the PR body and testing-planner's review has no blockers.
- CI is green.

## Related Tickets
Dependabot #572, #573, #574, #575.

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1, step 2)

## Related Stored Artifacts
None.

## Related Code Areas
`.github/workflows/{test,slow-regression,slow-regression-watchdog,rpg-gate-report,deploy-docs,pr-body-lint}.yml` (not platform-owned; edits only bump action majors)

## Assumptions / Open Questions
A workflow_dispatch run and the push of this branch are remote actions that need the user's authorization.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
