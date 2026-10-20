---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-PR-BODY-LINT-PIN-CHECKOUT-BY-SHA
phase: open
date: 2026-10-20
tags: [ai, process-improvement, governance]
---

# TCK-20261020-PR-BODY-LINT-PIN-CHECKOUT-BY-SHA

## Title
pr-body-lint.yml pins actions/checkout by full commit SHA, per the repo-wide pin rule

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
`.github/workflows/pr-body-lint.yml:17` still uses `actions/checkout@v7`, a mutable tag. agent-working owns this workflow, per `registries/session_roles.yaml`.

#668 recorded the repo-wide rule: every action is pinned by full commit SHA plus a `# vX.Y.Z` comment. #675's static guard (`tests/static/test_workflow_actions_pinned_by_sha.py`) covers only testing's four workflows, so this one passes CI unguarded. Every other workflow on main uses `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`.

perf-planner spotted it; lead-planner relayed it on 2026-10-20.

## Scope
1. In `.github/workflows/pr-body-lint.yml`, change `uses: actions/checkout@v7` to `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`, the same pin main uses everywhere else. No other change to the workflow.
2. Add a guard in `tests/tools/`, owned by agent-working, asserting that every `uses:` in `pr-body-lint.yml` is a 40-hex SHA plus a `# vX.Y.Z` comment, with local `./` actions exempt.
   - Reuse `unpinned()` from `tests/static/test_workflow_actions_pinned_by_sha.py` if it imports cleanly from tests/tools.
   - Otherwise copy the same two regexes, with a comment naming the source.
   - Don't edit testing's guard file; it belongs to testing.

## Out of Scope
- Other workflows. They're already pinned and owned by other seats.
- Extending testing's guard repo-wide. That's an fyi to testing-planner, not this ticket.
- The Ubuntu 26 runner question (#631).

## Acceptance Criteria
- `git grep 'actions/checkout@v' -- .github/workflows` is empty on the branch.
- The new guard passes, and fails on a `@v7` line (a unit case on a literal string).
- tests/static, tests/architecture and tests/docs pass, because a workflow changed (head/base parity). The PR's pr-body-lint run passes on the pinned checkout.

## Related Tickets
- TCK-20261019-TEST-WORKFLOWS-PIN-ACTIONS-BY-SHA (#675, the guard and pin format)
- #668 (platform: the repo-wide pin rule)
- #631 (CI runner migration, per workflow owner)

## Related Docs
- docs/guides/delivery_process.md (PR body lint)

## Related Stored Artifacts
- none

## Related Code Areas
- .github/workflows/pr-body-lint.yml, tests/static/test_workflow_actions_pinned_by_sha.py, tests/tools/

## Assumptions / Open Questions
- v7.0.1 at 3d3c42e5 is the pin already used across main, so this one simply matches it. Dependabot keeps the pins current.

## Implementation Notes
- 2026-10-20 (agent-working-planner): folded into batch 6 with TCK-20261020-HAND-CLOSURE-RECORDS-FOLDED-PHASES-AS-SKIPPED.

## Test Summary

## Files Changed

## Completion Summary
