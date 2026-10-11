---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED
phase: done
date: 2026-10-10
tags: [ai, governance, delivery]
---

# TCK-20261010-PR-BODY-LINT-WORKFLOW-UNOWNED

## Title
`.github/workflows/pr-body-lint.yml` routes to no domain after #476

## Status
DONE

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
Added `.github/workflows/pr-body-lint.yml` to agent-working's `owns` in `registries/session_roles.yaml`, next to `tools/delivery/**`. The agent-working planner card then exceeded the 400-token budget (411), so the two session registry files collapsed into the glob `registries/session_*.yaml`, which matches exactly `session_roles.yaml` and `session_authority.yaml` today (the only `session_*` files in `registries/`); the three agent-working cards are now 383/400/389 tokens. Owner to confirm the literal diff (governing file); note the glob would also own a future `registries/session_*.yaml`.

## Test Summary
`route.py .github/workflows/pr-body-lint.yml` -> owned, domain agent-working. Routing of both registry files unchanged. `tools.sessions.validate`: 0 findings, 17 roles. `generate_agents --check`: 0 drift. Session cards/roster/route/generator/settings_freshness tests: 113 passed.

## Files Changed
`registries/session_roles.yaml`, `.claude/agents/session-agent-working-{designer,implementer,planner}.md` (regenerated).

## Completion Summary
pr-body-lint.yml now routes to the agent-working domain.
