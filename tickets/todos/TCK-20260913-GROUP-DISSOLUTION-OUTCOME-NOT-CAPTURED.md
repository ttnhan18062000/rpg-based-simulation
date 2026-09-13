---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED
phase: open
date: 2026-09-13
tags: [cognition, social]
---

# TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED

## Title
Dissolved groups are removed from state outright — nothing captures whether the recruitment that formed them worked out

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Filed while implementing `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` (contract →
group reverse lookup), per peer's explicit instruction to disclose this as a real, separate gap
rather than leave it in that PR's description.

`GroupSystem.update_groups()` (`src/systems/world_systems/groups.py`) removes a group from
`state.groups` entirely (`groups_remove`) the moment it drops below 2 members — confirmed via
grep: no code path anywhere retains a dissolved group in a queryable form afterward.
`GroupRecord.dissolution_tick` (`src/core/state.py`) is a declared field that no write site ever
sets — dead at the data-model level, not just unused.

This means `GroupSystem.find_group_for_contract()` (the function this ticket's origin added) can
only ever answer "is this contract's recruitment currently a live group" — the moment the group
dissolves (recruit dies, contract expires, cohesion breaks, betrayal, whatever), the record is
gone and the question "did this recruitment ever produce a group, and how did it end" becomes
unanswerable after the fact. That is the real blocker for any future contract-outcome
differentiation (e.g. distinguishing "recruit died in the field" from "recruit betrayed the
contract" from "contract simply expired") — durable event history, not a live-state query, is
what that kind of work would need.

## Scope
This ticket is scoped as **the question, not a mechanism**: should group dissolution capture a
durable outcome record, and if so, what should it contain and where should it live? The right
shape (a lightweight terminal-state event, a `dissolution_tick` + `dissolution_reason` populated
in place before removal, a separate durable log, something else) depends on what the eventual
contract-outcome/differentiation work actually needs to query — which is not designed yet. Do not
build a specific mechanism speculatively; investigate what durable-state precedents exist elsewhere
in the codebase for "an entity/record left the active set but its outcome still matters"
(e.g. how entity death outcomes are recorded, if at all) and bring options back before implementing.

## Out of Scope
- Any specific persistence mechanism, chosen without first confirming what the differentiation
  work needs.
- Re-deriving outcomes retroactively from other logs (chronicle/event history) as an alternative
  to capturing it at dissolution time — that's a legitimate option to weigh, not a foregone
  conclusion, and should be evaluated alongside the others during investigation.
- Actually building contract-outcome differentiation (betrayal vs. death vs. expiry) — this ticket
  only unblocks that by making the outcome observable, it doesn't do the differentiation itself.

## Acceptance Criteria
- [ ] Investigation surveys existing durable-outcome precedents in the codebase (if any) before
      proposing a shape.
- [ ] A concrete design question (not yet a decision) is brought to peer/user: what to capture at
      dissolution, and where it should live, with real options and a recommendation.
- [ ] No implementation proceeds until that design question is answered.

## Related Tickets
- `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` (origin — implementing the
  contract→group reverse lookup surfaced this as the boundary of what that lookup can answer)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/systems/world_systems/groups.py` (`GroupSystem.update_groups()`, where `groups_remove`
  drops a dissolved group from `state.groups` with no trace left behind)
- `src/core/state.py` (`GroupRecord.dissolution_tick` — a declared, never-written field)

## Assumptions / Open Questions
- The real capture mechanism is the central, deliberately-unresolved question this ticket exists
  to answer — not assumed here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
