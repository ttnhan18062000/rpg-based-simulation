---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261014-ACTIONS-MAJORS-COMBINED
phase: inprogress
date: 2026-10-14
tags: [platform]
---

# TCK-20261014-ACTIONS-MAJORS-COMBINED

## Title
Land the GitHub Actions majors (#572-#575) as one verified PR, with testing-planner's artifact proof

## Status
INPROGRESS

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
  2. The PR run's artifact list shows test.yml's 3 artifacts (incl. `perf-tripwire`), each with its files present
     (check hidden/dotfile paths and `if-no-files-found`).
  2b. slow-regression.yml runs only on schedule/dispatch, and a dispatch costs about 2 runner-hours. **No dispatch**
     (testing-planner, 2026-10-14). Its 2 uploads use the same upload-artifact@v7 step shape, so the test.yml proof covers
     the action. The PR body must say: testing-planner verifies `certification-report-<sha>` and `slow-junit-<sha>` on
     the first scheduled slow run on main after merge (artifacts exist with files, and the report step finds the
     JUnit); if both are missing, the merge gets reverted.
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
Re-applied exactly the four Dependabot diffs (#572-#575) with `sed`, keeping the tag-pin style: `actions/checkout` v4/v5 -> v7 (30 uses: deploy-docs 1, pr-body-lint 1, rpg-gate-report 4, slow-regression-watchdog 1, slow-regression 2, test.yml 21), `actions/upload-artifact` v4 -> v7 (7 uses: test.yml 3, slow-regression 2, rpg-gate-report 2), `actions/download-artifact` v4 -> v8 (rpg-gate-report 1), `actions/upload-pages-artifact` v3 -> v5 (deploy-docs 1). The counts match the four Dependabot diffs. `publish-images.yml` is untouched (its actions are SHA-pinned).

Audit (no workflow logic changed):
- **Hidden paths:** none of the uploads write dotfiles or dot-directories. Paths are `reports/junit/<job>*.xml` (test.yml), `reports/certification/` and `reports/slow/` (slow-regression), `gate-docs/` and `report/` + `gate-docs-rerun/` (rpg-gate-report); the harness names documents `<world>__s<seed>.json` / `<world>__pooled.json` plus `<doc>.cost.json` sidecars, none starting with `.`. `include-hidden-files` is unset everywhere, which is fine for that reason.
- **Duplicate artifact names:** none. Names are `<job>-junit-<sha>` (3), `certification-report-<sha>`, `slow-junit-<sha>`, `rpg-gate-docs-<world>` (matrix, unique per world) and `rpg-gate-report-<sha>`.
- **`if-no-files-found`:** unset on all uploads (default `warn`): a missing file is a warning, not a failure. Reported to testing; not changed here.
- **`download-artifact` in rpg-gate-report** uses `pattern: rpg-gate-docs-*` into `gate-docs` with no `merge-multiple`, same as at v4; the dispatch run is the proof that the report finds the per-world docs.
- **Finding for testing-planner:** the ticket's evidence items 2 and 3 name a `perf-tripwire` artifact and a second checkout into `perf-base`. Neither string exists in any workflow on this branch (`grep -rn perf-tripwire\|perf-base .github/workflows` finds nothing); test.yml's three uploads are `tools-a-e-junit-<sha>`, `tools-f-z-junit-<sha>` and `api-cli-engine-junit-<sha>`. So items 2 and 3 as worded cannot be shown on this PR; testing-planner needs to restate them or confirm they live on another branch.
## Test Summary
- **validated (local):** actionlint runs on all workflows with no finding about the four actions (it reports only pre-existing shellcheck style notes in test.yml and others, unrelated to this change).
- Not yet run: the PR's CI, the `rpg-gate-report.yml` `workflow_dispatch` on this branch (needs the user's yes), and testing-planner's review. `deploy-docs.yml` runs only on main, so #574 and the checkout bump in that file cannot be proven on the PR; the owner watches the first main run. `slow-regression.yml` runs only on schedule or dispatch, and a dispatch costs about 2 runner-hours, so there is no dispatch: testing-planner verifies `certification-report-<sha>` and `slow-junit-<sha>` on the first scheduled slow run on main after merge (artifacts exist with files, and the report step finds the JUnit); if both are missing, the merge gets reverted.
## Files Changed
- `.github/workflows/{deploy-docs,pr-body-lint,rpg-gate-report,slow-regression-watchdog,slow-regression,test}.yml` (version tags only)
## Completion Summary
