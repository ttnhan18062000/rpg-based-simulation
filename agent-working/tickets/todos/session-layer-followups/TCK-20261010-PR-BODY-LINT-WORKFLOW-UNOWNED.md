---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED
phase: open
date: 2026-10-10
tags: [ai, governance, delivery]
---

# TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED

## Title
`.github/workflows/pr-body-lint.yml` routes to no domain after #476

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
PR #476 meant `pr-body-lint.yml` to "stay with delivery", but no domain's `owns` covers it.
`python3 -m tools.sessions.route .github/workflows/pr-body-lint.yml` still answers
`status: unowned`. Every other workflow has an owner: testing owns `test.yml` and
`slow-regression*.yml`, and lead owns `deploy-docs.yml`.

## Scope
Add `.github/workflows/pr-body-lint.yml` to the agent-working domain's `owns`, next to
`tools/delivery/**`. Regenerate any derived files the validator requires.

## Out of Scope
Any change to the workflow itself.

## Acceptance Criteria
1. `route.py .github/workflows/pr-body-lint.yml` names the agent-working domain.
2. `python3 -m tools.sessions.validate` reports 0 findings.
3. The owner confirms the literal `registries/session_roles.yaml` diff (governing-file class).

## Related Tickets
- `TCK-20261009-REGISTER-OTHER-HOST-SEATS` (PR #476)

## Related Docs
- `docs/guides/delivery_process.md` (PR Lifecycle, PR-body lint)

## Related Stored Artifacts
None.

## Related Code Areas
`registries/session_roles.yaml`

## Assumptions / Open Questions
None.

## Implementation Notes
(Open.)

## Test Summary
(Open.)

## Files Changed
(Open.)

## Completion Summary
(Open.)
