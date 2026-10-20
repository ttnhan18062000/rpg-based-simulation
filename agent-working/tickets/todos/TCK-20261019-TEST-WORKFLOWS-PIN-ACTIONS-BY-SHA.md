---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-TEST-WORKFLOWS-PIN-ACTIONS-BY-SHA
phase: open
date: 2026-10-19
tags: [testing, workflows]
---

# TCK-20261019-TEST-WORKFLOWS-PIN-ACTIONS-BY-SHA

## Title
testing's workflows pin every action by full commit SHA with a `# vX.Y.Z` comment, setup-node moves to its current major, and a static test keeps every ref a SHA.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
**Owner decision, 2026-10-19,** relayed by lead-planner-u24 and platform-planner-u24: every workflow pins actions by full commit SHA with a `# vX.Y.Z` comment, GitHub-owned actions included. Dependabot github-actions keeps them current (grouped, monthly).

#609 (the actions-major group) is closed by the owner's choice. Each action is pinned straight to its newest major. For testing that means `actions/setup-node` v4 goes to v7.

This clears Semgrep `github-actions-mutable-action-tag`:
- 43 in test.yml;
- 6 in slow-regression*.yml;
- 9 in rpg-gate-report.yml.
Source: security-scan main run 39233931697.

Scope is testing's files only. pr-body-lint.yml is agent-working's (TCK-20261019-SEMGREP-BASELINE-AGENT-WORKING-PATHS), and deploy-docs.yml is platform's. platform records the rule in delivery_process.md.

## Scope
1. In `.github/workflows/test.yml`, `slow-regression.yml`, `slow-regression-watchdog.yml` and `rpg-gate-report.yml`, every `uses:` becomes `owner/repo[/path]@<40-hex SHA> # vX.Y.Z`. On main today that is:
   - checkout@v7, upload-artifact@v7, download-artifact@v8 and setup-uv@v10.3.0;
   - setup-node@v4, which goes to **v7**;
   - codeql-action/upload-sarif, which is already a SHA: add its `# vX.Y.Z` comment.
2. **Reuse platform's SHAs** where the action and version match: checkout `3d3c42e5…` (# v7.0.1) and upload-artifact `cf430e03…` (# v7.0.2), taken from platform's workflows on main. Copy the full 40-hex values.
   - For every other action, resolve the SHA of the release tag with `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`. Dereference an annotated tag to its commit.
   - Record each action → SHA → version in Implementation Notes.
   - **Check every SHA against its tag ref, the reused platform ones too** (lead-planner-u24, 2026-10-20): `gh api repos/<owner>/<repo>/git/ref/tags/<vX.Y.Z>`, dereferencing an annotated tag. The pinned SHA must equal the tag's commit. Paste the check output in Implementation Notes. The pin form is the one platform's #668 uses: full SHA + `# vX.Y.Z`.
3. **setup-node v7:** check the v7 release notes for input changes. `node-version: 24` (#655), `cache: npm` and `cache-dependency-path` must keep working. If an input changed, stop and report.
4. **Static guard:** a test over these four workflows fails on any `uses:` that is not a 40-hex SHA followed by a `# v` comment, except local `./` actions. Add a regression snippet.
5. **Existing pins:** the CI-runtime and tools static tests (`test_ci_xdist_in_critical_path_jobs.py`, `test_ci_split_tools_jobs.py`, `test_ci_step_summary_reporting.py` and similar) match actions by NAME. Run them. If any matches a ref literally, change it to match by name, as TCK-20261015-SETUP-UV-PIN did.
6. **Dependabot:** confirm `.github/dependabot.yml` has the github-actions ecosystem grouped, monthly. If not, route that change to its owner. Don't edit it here unless route says testing owns it.

## Out of Scope
- pr-body-lint.yml (agent-working) and deploy-docs.yml (platform).
- Any change to what a step does.
- The rule's doc line (platform's ticket).

## Acceptance Criteria
- [ ] AC1: in the four workflows, every `uses:` is a 40-hex SHA plus a `# vX.Y.Z` comment. The guard test proves it and fails on its regression snippet.
- [ ] AC2: checkout and upload-artifact use the same SHAs as platform's workflows on main.
- [ ] AC3: setup-node is v7. CI's Frontend job and the jscpd step still log Node v24.x; quote the line.
- [ ] AC4: CI on the PR is green, including the changed-files gate. test.yml's job count is unchanged.
- [ ] AC5: the first security-scan main run after merge shows 0 `mutable-action-tag` findings in these four files. Quote the run id (a post-merge check).

## Related Tickets
- TCK-20261019-TEST-WORKFLOWS-GITHUB-CONTEXT-VIA-ENV-NOT-RUN (#667, MERGED e52719485 on 2026-10-20; this ticket is unblocked)
- TCK-20261019-TEST-YML-NODE-24-IN-FRONTEND-AND-JSCPD-LANES (#655, node-version 24)
- TCK-20261015-SETUP-UV-PIN-IN-SPLIT-TOOLS-JOBS-TEST-BLOCKS-DEPENDABOT (match by name)
- TCK-20261019-SESSION-ROLES-OWN-UNOWNED-SEMGREP-PATHS (registers rpg-gate-report.yml to testing)

## Related Docs
- docs/guides/delivery_process.md (platform adds the rule)

## Related Stored Artifacts
- (none)

## Related Code Areas
- .github/workflows/test.yml, slow-regression.yml, slow-regression-watchdog.yml, rpg-gate-report.yml
- tests/static/

## Assumptions / Open Questions
- rpg-gate-report.yml is in scope by the owner's direction even if the roles PR hasn't merged yet. rpg-planner agrees it isn't theirs.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
