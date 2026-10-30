---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-RULESET-EXPORT-AND-LOGIN-ASSUMPTION-INVENTORY
phase: open
date: 2026-10-31
tags: [ai, governance, delivery]
---

# TCK-20261031-SDLC-RULESET-EXPORT-AND-LOGIN-ASSUMPTION-INVENTORY

## Title
The ruleset is exported as the rollback point, and the tools that assume the owner's login are listed.

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Plan section 54 items 3-4, required before any credential change. Both are read-only.

## Scope
1. Export the production ruleset JSON, read-only, into a committed artifact, with SHA and date.
2. Inventory the tools and scripts that assume the owner login or need admin-only endpoints (`pr_render`, `pr_status`, GitHub MCP configuration, scripts calling `gh api`), recording what each would do under a write-role machine user.
3. Re-check that there are no repository-level Actions secrets, reporting names only.

## Out of Scope
- Host credential stores and E6a step 3: reported to the owner only, never in this ticket's artifacts.
- Changing any tool or setting.

## Acceptance Criteria
1. The export parses, and can be compared against a fresh read.
2. Each inventoried tool has a stated behaviour under the machine user, by trace or stated as unverified.
3. No credential value, store location or host detail in any artifact.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/delivery/pr_render.py, tools/delivery/pr_status.py
- agent-working/stored_artifacts/ (result record)

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
