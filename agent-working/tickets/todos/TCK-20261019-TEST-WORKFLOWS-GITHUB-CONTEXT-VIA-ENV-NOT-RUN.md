---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-TEST-WORKFLOWS-GITHUB-CONTEXT-VIA-ENV-NOT-RUN
phase: open
date: 2026-10-19
tags: [testing, workflows]
---

# TCK-20261019-TEST-WORKFLOWS-GITHUB-CONTEXT-VIA-ENV-NOT-RUN

## Title
testing's workflows pass `${{ github.* }}` values to shell steps through `env:`, never interpolated into `run:`, and a static test keeps it that way.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
platform-planner-u24's new report-only security-scan.yml (#665, main run 39233931697, SARIF "semgrep") reports 11 `run-shell-injection` findings in `.github/workflows/test.yml`.

testing-planner triaged them on 2026-10-19: none can be exploited today. The interpolated values are `github.base_ref` (a branch of this repo), `github.event_name`, and the PR base/head SHAs. None is free text an attacker controls, such as a head_ref, title or body.

Moving them to `env:` is still the cheap and correct pattern. It clears the alerts, and it stops the pattern being copied the day someone interpolates `head_ref` or a title.

## Scope
1. In `.github/workflows/test.yml`, every `${{ github.* }}` inside a `run:` block becomes a step-level `env:` variable that the script uses as `"$VAR"`. Cover:
   - the `git fetch origin "${{ github.base_ref }}"` lines in each job;
   - the changed-files gate's `event_name`, `base.sha` and `head.sha`;
   - the L1100/L1101 and L1150 diff lines.
   Leave `name:`, `if:`, `concurrency:` and `with:` uses alone; they are not shell.
2. Do the same in `slow-regression.yml` and `slow-regression-watchdog.yml` if any exist there (Semgrep reported none).
3. Add a static test, `tests/static/test_workflow_run_blocks_take_github_context_via_env.py`, over testing's workflows (test.yml, slow-regression*.yml). It fails if any `run:` string contains `${{ github.` or `${{ inputs.`, and it includes a regression case on an in-memory YAML snippet.
4. Behaviour is unchanged: same commands, same values.

## Out of Scope
- Pinning actions by SHA. The 43 + 6 `mutable-action-tag` findings wait on a repo-wide pin policy (platform-planner and lead), because the same choice applies to every workflow and to Dependabot's update flow. testing follows that policy once it exists.
- Workflows testing does not own.

## Acceptance Criteria
- [ ] AC1: `grep -n '\${{ *github\.' .github/workflows/test.yml` shows no hit inside a `run:` block.
- [ ] AC2: the new static test passes on the branch and fails on its regression snippet.
- [ ] AC3: CI on the PR is green, including the changed-files gate. The gate's "changed files" output for the PR lists the same files it would have listed before the change; quote it.
- [ ] AC4: the first main-push run after merge shows the security-scan's semgrep `run-shell-injection` count for test.yml at 0. Quote the run id.

## Related Tickets
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS (the changed-files gate)

## Related Docs
- docs/guides/delivery_process.md

## Related Stored Artifacts
- (none)

## Related Code Areas
- .github/workflows/test.yml, slow-regression.yml, slow-regression-watchdog.yml
- tests/static/

## Assumptions / Open Questions
- Semgrep's 11 count may include lines this grep misses (multi-line `run:`). The static test is the authority: it parses the YAML.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
