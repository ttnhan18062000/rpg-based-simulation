---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE
phase: open
date: 2026-07-01
tags: [simq, event-emission, social, contract, scoring, schema]
---

# TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE

## Title
Wire contract_milestone_completed emitter: add milestones field to ContractState

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`contract_milestone_completed` is a SocialScorer event type (+3 `contract_honored` signal)
that cannot be emitted because `ContractState` has no `milestones` field. The contract
system tracks overall contract lifecycle (OFFERED → ACTIVE → FULFILLED/EXPIRED) but does
not model intermediate milestones, so there is no state to diff for partial completions.

This is the lower-priority §3.8 gap. The contract system must be extended with a milestone
concept before an emitter can be written.

## Scope
1. Investigate `src/core/state.py` or `src/domains/social/` — find `ContractState`; confirm
   what fields exist and whether any milestone concept is present.
2. If no milestone field exists:
   a. Add `milestones_completed: frozenset[str]` (or `int`) to `ContractState` — immutable,
      consistent with durable state rules.
   b. Confirm the authoritative apply pipeline (PP-35 `active_contracts`) updates this field.
3. Add milestone detection in `event_extractor.py`: diff `milestones_completed` between
   prior and current state; emit `contract_milestone_completed` per new milestone.
4. If a milestone concept already exists under a different name, use that instead of
   adding a new field.
5. Unit tests: milestone set grows → event emitted; milestone set unchanged → no event.

## Out of Scope
- Redesigning the contract execution system
- Adding a milestone scheduling / trigger system
- Changing SocialScorer weights

## Acceptance Criteria
- [ ] `ContractState` has a field that tracks completed milestones
- [ ] `contract_milestone_completed` emitted when new milestones appear in state diff
- [ ] Event reaches SocialScorer
- [ ] Parity ledger updated
- [ ] `event_type_coverage.md §3.8` updated — `contract_milestone_completed` row removed
- [ ] No regression in existing contract/social tests

## Related Tickets
- TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY — identified the block
- TCK-20260628-SIMQ-EPIC — parent epic

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.8`
- `docs/simulation_quality/quality_scoring_contract.md §5 SOCIAL`
- `docs/parity_ledger/social_narrative.yaml`

## Related Code Areas
- `src/core/state.py` — ContractState definition
- `src/observability/event_extractor.py` — where contract events are emitted
- `src/engine/pipeline_phases/` — PP-35 active_contracts phase

## Assumptions / Open Questions
- ContractState may already have partial tracking under a different name (e.g.
  `fulfilled_obligations`, `completed_phases`). Check before adding a new field.
- Milestone IDs may not exist in the current schema — clarify whether milestones
  are string IDs or ordinal integers.
- If ContractState is frozen/immutable, the update must go through StateUpdate.

## Test Summary
- Unit: prior ContractState has no milestones → current has one → event fires
- Unit: milestone already present → no event (no double-fire)
- Unit: payload includes contract_id and milestone_id

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
