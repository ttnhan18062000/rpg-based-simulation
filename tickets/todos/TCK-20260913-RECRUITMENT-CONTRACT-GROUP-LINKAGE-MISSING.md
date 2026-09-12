---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING
phase: open
date: 2026-09-13
tags: [cognition, social]
---

# TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING

## Title
A recruitment contract produces a `GroupRecord`, but nothing records which group a given contract produced — no way to go from a contract to "did this recruitment actually work out"

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION`'s own
investigation, while checking whether `PartyCohesionService`'s real `MEMBER_ABANDONING`/
`LEADER_LOST` signal (`src/domains/cooperation/services.py:327-379`, evaluated every tick for every
active group in `CooperationPhase.execute()`) could serve as a real, live "did this contract's
recruitment work out" signal for contract-outcome resolution.

Checked `ContractState.terms` for every real recruitment-contract construction site
(`ContractService.create_recruitment_contract()`, `src/systems/social_systems/contracts.py:112-135`):
`{"daily_pay": ..., "duration": ..., "risk_level": ...}` — no `group_id` field, no reference to the
`GroupRecord` a fulfilled `JOIN_PARTY` accept (`TCK-20260912-PARTY-FORMATION-REACHABILITY-
INVESTIGATION`) would have formed from it. `GroupRecord` itself (`state.groups`) has no reverse
reference to the contract that produced it either. The only way to associate a contract with a
group today is inference: matching `contract.source_id`/`.target_id` against a group's
`leader_id`/`member_ids` — not stored, not maintained, and ambiguous once either party is in more
than one contract or has changed groups since the contract was created.

This is the prerequisite for any outcome-based social consequence keyed off real party cohesion
(cross-referenced from `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION`,
regardless of how that ticket's own dual-mechanism disposition lands) — without it, "did this
contract's recruitment actually work out" has no real, non-inferred answer.

## Scope
- Determine the real fix: store a `group_id` (or equivalent reference) on `ContractState` when a
  recruitment contract's `JOIN_PARTY` accept actually forms/extends a `GroupRecord`, or maintain
  a reverse index from contract to group elsewhere — real design work, not assumed here.
- Confirm the timing: at what point in the pipeline does a `GroupRecord` actually get created from
  an accepted `RECRUITMENT` contract (`GroupSystem.update_groups()`,
  `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`'s own fix), and is that the right
  moment to also write the linkage.
- Real test evidence the linkage is populated and queryable for a real recruitment contract that
  genuinely forms a group.

## Out of Scope
- Whatever disposition `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION`
  reaches on its own dual-mechanism question — this ticket is the prerequisite either way, not
  contingent on that determination.
- Contract kinds other than `RECRUITMENT` (the only kind that forms a `GroupRecord` today) unless
  Investigate finds a real reason to widen.

## Acceptance Criteria
- [ ] Real evidence on exactly when/where a `GroupRecord` is formed from an accepted recruitment
      contract.
- [ ] A peer-routed decision on the real linkage mechanism (field on `ContractState`, reverse
      index, or other), obtained before implementation.
- [ ] Real test evidence the linkage is populated for a genuine recruitment→group formation and
      queryable afterward.
- [ ] No regression in `tests/unit/domains/cooperation/`, `tests/integration/domains/cooperation/`.

## Related Tickets
- `TCK-20260912-CONTRACT-EXPIRY-DUAL-MECHANISM-DETERMINATION` (done — origin — found
  while checking whether cohesion could drive contract-outcome resolution)
- `TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION` (the ticket that wired `JOIN_PARTY`
  accept → real `GroupRecord` formation; this ticket's own timing question depends on that fix)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

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
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
