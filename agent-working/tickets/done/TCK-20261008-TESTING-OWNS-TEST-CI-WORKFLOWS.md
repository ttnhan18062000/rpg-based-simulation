---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261008-TESTING-OWNS-TEST-CI-WORKFLOWS
phase: done
date: 2026-10-08
tags: [workflows]
---

# TCK-20261008-TESTING-OWNS-TEST-CI-WORKFLOWS

## Title
The testing domain owns the test CI workflows and tools/test_architecture/

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner assignment on 2026-10-08, relayed by testing-planner: "from now, you hold the git CI testing as well, not just test architecture". The owner confirmed the scope to agent-working-planner as "test CI only". Before this change, no domain owned `.github/workflows/` or `tools/test_architecture/`.

## Scope
`registries/session_roles.yaml`: the testing domain owns `.github/workflows/test.yml`, `.github/workflows/slow-regression*.yml` (this includes slow-regression-watchdog.yml from PR #435, at testing-planner's request) and `tools/test_architecture/**`. The codebase domain routes `tools/test_architecture/**` to testing-planner, ahead of its general `tools/**` route. Role cards regenerated.

## Out of Scope
`pr-body-lint.yml` stays unowned in the manifest (delivery lane, agent-working by practice); `deploy-docs.yml` stays unowned. No change to session_authority.yaml (the actions are unchanged).

## Acceptance Criteria
1. `route.py` resolves the three paths to the testing domain from the rpg, codebase and agent-working domains.
2. `validate.py` passes; every role card stays within its token budget.
3. Scoped session tests pass, apart from 2 failures that predate this change (`test_session_layer_measures`, which also fail without it).

## Related Tickets
TCK-20261008-SLOW-REGRESSION-SCHEDULE-WATCHDOG (the first work under this ownership)

## Related Docs
docs/guidelines/session_roles/

## Related Stored Artifacts
None.

## Related Code Areas
registries/session_roles.yaml, .claude/agents/session-*.md

## Assumptions / Open Questions
Routes were added only where needed. Adding them to every domain pushed agent-working and rpg cards over the 400-token budget, and an owned path already resolves without a route except where a broader route (codebase `tools/**`) would win.

## Implementation Notes
Hand-orchestrated by agent-working-planner.

## Test Summary
validate OK (0 findings); test_session_cards 37 passed; scoped tests/tools session suite: 827 passed, 2 failed (pre-existing in test_session_layer_measures, reproduced without the change).

## Files Changed
registries/session_roles.yaml; .claude/agents/session-*.md (regenerated)

## Completion Summary
The testing domain now owns the test CI workflows and their helpers; routing verified from each domain.
