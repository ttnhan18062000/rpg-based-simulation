---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS
phase: open
date: 2026-10-31
tags: [ai, governance, delivery]
---

# TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS

## Title
Research stage R0: candidate tasks and the disposition review are recorded, and baselines are frozen as git tags.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
R0 (plan section 70). OD-15 is decided yes: freeze baselines as tags. R0 is read-only apart from the tags, and it must land before Phase 4 so retirement cannot remove a useful baseline.

## Scope
1. Candidate tasks from recent closes, against the plan's admissibility rules (section 66), enough to expect 6-8 tasks.
2. The disposition review (section 32a).
3. Billing and subscription limits: ask the owner; record only what the owner agrees to publish.
4. Baseline tags: list the exact tag names and SHAs, then ask the owner through lead-planner to push them. A tag push is visible to others and has its own ask.

## Out of Scope
- R1 runner, trials, or any model comparison.
- OD-16 to OD-21, including the budget.
- The tag ruleset (see the ruleset ticket). Until then tags are not protected; say so in the record.

## Acceptance Criteria
1. The candidate list has task count, source close and admissibility verdict per task.
2. Every section 32a row has a disposition.
3. Tags exist at the recorded SHAs on the remote, after the owner's yes.
4. The record states what is still needed before R1 (OD-16, 17, 18, 21).

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- .claude/workflows/, tools/agent_orchestration/, tools/agent_replay* (read-only)
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
