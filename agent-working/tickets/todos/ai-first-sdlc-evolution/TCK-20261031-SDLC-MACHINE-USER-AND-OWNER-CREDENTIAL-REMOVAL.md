---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-MACHINE-USER-AND-OWNER-CREDENTIAL-REMOVAL
phase: open
date: 2026-10-31
tags: [ai, governance, security]
---

# TCK-20261031-SDLC-MACHINE-USER-AND-OWNER-CREDENTIAL-REMOVAL

## Title
Agents authenticate as a machine user on both hosts, and owner credentials are gone from both hosts and revoked.

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 1 execution (plan sections 27a and 39). OD-2 and OD-10 are decided yes, and OD-14 sets the rollback: agents never regain the owner's token. Authorised by none of this: execution has its own owner ask. BLOCKED until the conditions below hold.

## Scope
Unblock conditions, all required:
- E6b reported, and M1 still holds.
- Ruleset export and login inventory done.
- A confirmed path for both hosts to change on the same day.
- OD-13's `workflow` scope question answered: the token's scopes depend on it.
- Owner's own yes for this execution.

Then, led by the owner: create the machine user and one expiring token per host; move agent sessions onto it; remove owner credentials and revoke every pre-existing one (E6a step 4); fix what the inventory found; run E6a with the owner present; its inventory covers the two details still unread on u24, reported to the owner only.

## Out of Scope
- Ruleset changes (the ruleset ticket).
- Other projects on these hosts: the owner's call.

## Acceptance Criteria
1. Phase 1 acceptance (plan section 39): an agent can push a branch and open a PR; it cannot merge, push to main or approve its own PR, with GitHub rejecting each attempt.
2. No owner credential is usable from either host.
3. The owner merges a scratch PR from outside the hosts.
4. New PRs are authored by the machine user, and `current_user_can_bypass` reads `never`.
5. No credential detail in a committed file, ticket or public comment; reports go to the owner.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- gh auth on both hosts (owner-led)
- tools/delivery/ per the inventory

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.
- OD-7 (review load) is open and follows from OD-3 and E6b.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
