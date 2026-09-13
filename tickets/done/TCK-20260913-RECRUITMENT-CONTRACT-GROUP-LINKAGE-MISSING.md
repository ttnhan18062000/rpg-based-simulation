---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING
phase: done
date: 2026-09-13
tags: [cognition, social]
---

# TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING

## Title
Nothing maps a recruitment contract to the group it produced — the reverse direction is missing; the forward direction already exists

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
**Corrected 2026-09-13, before implementing: this ticket's own original framing was wrong.**
Filed claiming `GroupRecord` had "no reverse reference to the contract that produced it." Direct
investigation, done before writing any code, found this false in current code:
`GroupRecord.contract_id` (`src/core/state.py:669`) already exists and is already correctly
populated. `GroupSystem.update_groups()` (`src/systems/world_systems/groups.py:319`) sets it at
group-formation time to the real contract that drove the recruitment, write-once, never updated
afterward (confirmed via grep — no other write site). It's already load-bearing: the existing
group-invalidation check (`groups.py:136-144`) reads `leader.strategic.contracts.get(group.
contract_id)` to decide whether a group's founding contract is still valid. Whether this was
always true or was wired by `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION` (this
ticket's own dependency) isn't resolved here — what matters is that group→contract is real today.

Original context, still accurate: found during `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-
DETERMINATION`'s own investigation, while checking whether `PartyCohesionService`'s real
`MEMBER_ABANDONING`/`LEADER_LOST` signal (`src/domains/cooperation/services.py:327-379`) could
serve as a real, live "did this contract's recruitment work out" signal.

**The actual gap, narrower than originally filed: contract→group, the reverse direction.**
`ContractState` has no `group_id` field, and no index anywhere maps a contract to the group it
produced. Given a contract, there is still no real way to ask "which group did this form."

**A real limitation, disclosed rather than assumed away**: dissolved groups are physically removed
from `state.groups` (`groups_remove`, confirmed via grep — no dissolution-tick-marker-kept-around
pattern). Neither this ticket's own fix nor any contract→group lookup can answer "did this
contract's recruitment work out" *after* the group is gone — only while it's still alive. Capturing
a durable outcome at dissolution time is a real, separate gap, filed as its own ticket rather than
assumed into this one's scope: `TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED`.

## Scope
- Add a reverse-lookup function (`GroupSystem.find_group_for_contract(state, contract_id) ->
  Optional[GroupRecord]`), a plain scan over `state.groups.values()` matching `contract_id` —
  **not** a new stored field on `ContractState`. `GroupRecord.contract_id` is already the single
  source of truth for this relationship; mirroring it onto `ContractState` too would create a
  second, independently-writable copy of the same fact — the exact dual-mechanism shape this arc
  has spent multiple tickets deleting. Matches the real, already-established precedent in this
  codebase for the identical shape: `ClanLifecycleService.find_clan_id_for_entity()`
  (`src/systems/social_systems/clan_lifecycle.py`), a plain O(n) reverse scan, justified there by
  real group/clan counts being small in this repo's own fixtures.
- Real test evidence the lookup finds the right group for a genuine recruitment contract that
  forms one, and returns `None` for a contract that never formed a group.

## Out of Scope
- Whatever disposition `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION`
  reaches on its own dual-mechanism question — unrelated, that ticket is already closed.
- Contract kinds other than `RECRUITMENT` (the only kind that forms a `GroupRecord` today) unless
  Investigate finds a real reason to widen.
- Capturing contract-recruitment outcome durably past group dissolution — filed separately as
  `TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED`, not this ticket's own scope.

## Acceptance Criteria
- [x] `GroupSystem.find_group_for_contract()` implemented as a plain reverse scan, citing the
      `ClanLifecycleService.find_clan_id_for_entity()` precedent directly in the code comment.
- [x] Real test evidence: the lookup finds the correct group for a genuine recruitment→group
      formation, and returns `None` when no group was formed.
- [x] No regression in `tests/unit/domains/cooperation/`, `tests/integration/domains/cooperation/`,
      `tests/unit/social/` (groups.py's own existing test coverage, confirmed via
      `test_domain_7_social.py`).
- [x] `TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED` filed, cross-referenced in both
      directions, disclosing that this ticket's own fix only makes the linkage queryable while the
      group is alive, not durable past dissolution.

## Related Tickets
- `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION` (done — origin — found
  while checking whether cohesion could drive contract-outcome resolution)
- `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION` (the ticket that wired `JOIN_PARTY`
  accept → real `GroupRecord` formation; this ticket's own timing question depends on that fix)
- `TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED` (filed from this ticket's own disclosed
  limitation — this ticket only makes the linkage queryable while a group is alive, not durable
  past dissolution)

## Related Docs
None yet.

## Related Stored Artifacts
`stored_artifacts/TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING/` (investigation.md,
plan.md, test_plan.md)

## Related Code Areas
- `src/core/strategic.py` (`ContractState`, `GroupRecord`)
- `src/systems/social_systems/contracts.py` (`ContractService.create_recruitment_contract()`)
- `src/systems/world_systems/groups.py` (`GroupSystem.update_groups()`, where a `GroupRecord`
  actually gets formed)
- `src/domains/cooperation/services.py` (`PartyCohesionService.evaluate()`, the real cohesion
  signal this linkage would make usable for contract-outcome purposes)

## Assumptions / Open Questions
- The real linkage mechanism (field vs. index vs. something else) is the central,
  deliberately-unresolved question this ticket exists to answer — not assumed here.

## Implementation Notes
Corrected the ticket's own false original Request Summary before implementing anything — investigation
found `GroupRecord.contract_id` (group→contract) already existed, live and load-bearing (the
per-tick group-invalidation check reads it). The real gap was only the reverse direction. Two
design options considered for closing it: a mirrored `group_id` field on `ContractState` (Option B)
vs. a reverse-lookup function (Option A). Routed to peer; peer confirmed Option A specifically to
avoid building a second, independently-writable copy of the same fact — the dual-mechanism shape
this arc has spent multiple prior tickets deleting.

Implemented `GroupSystem.find_group_for_contract(state, contract_id) -> Optional[GroupRecord]`
(`src/systems/world_systems/groups.py`, immediately after `update_groups()`): a plain O(n_groups)
scan over `sorted(state.groups.items())`, matching `group.contract_id == contract_id`. Docstring
cites `ClanLifecycleService.find_clan_id_for_entity()` as the matched precedent for this exact
shape, and states the dissolution limitation directly.

Surfaced a real, disclosed limitation during investigation: dissolved groups are removed from
`state.groups` outright (`groups_remove`), so this lookup — and any contract→group lookup — can
only answer the question while the group is still alive, not after dissolution. Filed as its own
ticket per peer's instruction rather than left in this PR's description:
`TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED`, scoped as the open design question (what to
capture, where), not a chosen mechanism.

**Framing for the batch**: this ticket makes the linkage queryable while the group is alive, which
is real and enough for live checks, but it does not make recruitment outcomes durable — contract
failure/betrayal differentiation work depends on the sibling ticket resolving first.

## Test Summary
- `tests/unit/social/test_domain_7_social.py`: 7 passed (5 pre-existing + 2 new —
  `test_find_group_for_contract_returns_matching_group`,
  `test_find_group_for_contract_returns_none_when_no_group_formed`).
- `tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ tests/unit/social/
  tests/integration/campaigns/test_loyalty_pressure_campaign_bridge.py`: 336 passed, 0 failed —
  full regression across every suite exercising `GroupSystem`/`GroupRecord`.
- `python3 tools/validate_frontmatter.py` — passed for this ticket and the new sibling ticket.

## Files Changed
- `src/systems/world_systems/groups.py` — added `GroupSystem.find_group_for_contract()`.
- `tests/unit/social/test_domain_7_social.py` — added 2 tests.
- `tickets/inprogress/TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING.md` — corrected
  Request Summary/Scope/Out of Scope/Acceptance Criteria; closed.
- `tickets/todos/TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED.md` — new, filed.
- `staging_artifacts/TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING/` — new
  (investigation.md, plan.md, test_plan.md), moved to `stored_artifacts/` on close.

## Completion Summary
Implemented the contract→group reverse lookup as a plain, precedent-matching scan (Option A), after
correcting the ticket's own false original framing (group→contract already existed). Disclosed and
separately filed the real dissolution-outcome limitation this fix doesn't close. All acceptance
criteria met; zero regressions across 336 tests in the affected domains.
