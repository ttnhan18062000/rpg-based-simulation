---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-WORKFLOW-PIN-GUARD-COVERS-EVERY-WORKFLOW
phase: open
date: 2026-10-20
tags: [testing, workflows]
---

# TCK-20261020-WORKFLOW-PIN-GUARD-COVERS-EVERY-WORKFLOW

## Title
The SHA-pin guard globs every file in `.github/workflows/`, so one test enforces the repo-wide pin rule.

## Status
BLOCKED

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
lead-planner-u24's non-blocking follow-up on #675 (issuecomment-6281833519): `tests/static/test_workflow_actions_pinned_by_sha.py` lists only testing's four workflows. The owner's rule (SHA + `# vX.Y.Z`) applies to every workflow. Once the other owners' workflows are pinned, the guard should cover all of them.

**BLOCKED** until every other workflow on main is pinned:
- deploy-docs.yml: platform, #668.
- pr-body-lint.yml: agent-working, TCK-20261019-SEMGREP-BASELINE-AGENT-WORKING-PATHS.
- security-scan.yml and any other workflow: check on main when unblocking.

## Scope
1. Replace the `WORKFLOWS` tuple with a sorted glob of `.github/workflows/*.y*ml`, keeping the parametrized test per file.
2. Add a test that the glob finds at least the four testing workflows, so an empty glob cannot pass.
3. Optional (cheap): parse each file with yaml and assert the number of `uses` keys equals the number of regex matches, which closes the flow-style gap noted on #675.
4. Tell the owners of the other workflows (platform, agent-working) on the PR that the guard now covers their files.

## Out of Scope
- Pinning any workflow (each owner's).
- Dependabot config.

## Acceptance Criteria
- [ ] AC1: the guard covers every workflow file on main, and the test passes there.
- [ ] AC2: the non-empty-glob test exists. The existing regression snippets still fail as before.
- [ ] AC3: CI on the PR is green.

## Related Tickets
- TCK-20261019-TEST-WORKFLOWS-PIN-ACTIONS-BY-SHA (#675)
- TCK-20261019-SEMGREP-BASELINE-AGENT-WORKING-PATHS (agent-working, pr-body-lint.yml)

## Related Docs
- docs/guides/delivery_process.md (platform's pin rule)

## Related Stored Artifacts
- (none)

## Related Code Areas
- tests/static/test_workflow_actions_pinned_by_sha.py

## Assumptions / Open Questions
- Unblock check: `grep -nE 'uses:' .github/workflows/*.yml | grep -vE '@[0-9a-f]{40} # v'` on main returns nothing apart from local `./` actions.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
