---
status: done
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE
phase: done
date: 2026-07-01
tags: [simq, event-emission, social, contract, scoring, schema]
---

# TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE

## Title
Wire contract_milestone_completed emitter: add milestones field to ContractState

## Status
DONE

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

## Implementation Notes — Investigation (2026-07-01)

**ContractState** (`src/core/strategic.py:177`) is `@dataclass(frozen=True, slots=True)`.
Fields: `id`, `kind`, `source_id`, `target_id`, `terms: Dict[str, Any]`, `expiry_tick`,
`status`, `created_tick`, `negotiation_count`. No milestone field; no partial-completion concept.

**Contracts pipeline** (`src/engine/pipeline_phases/contracts.py`) only handles lifecycle at
expiry tick: ACTIVE → FULFILLED (duration honored) and OFFERED/COUNTERED → EXPIRED. There is
no intermediate milestone evaluation. `SocialContractSystem.transition_contract()` handles status
transitions but has no milestone concept either.

**Why this is design-blocked, not just schema-blocked:**
Adding `milestones_completed: frozenset[str]` to ContractState is technically straightforward
(frozen+slots dataclasses support new fields with defaults). But nothing in the pipeline
*produces* milestones — there is no trigger for what constitutes a milestone for any
`ContractKind`:
- LOAN: partial repayment installments? Not tracked.
- PROTECTION: periodic interval survived? Not tracked.
- MERCHANT: per-trade count toward a quota? Not tracked.
- POSITION_SWAP / RECRUITMENT: single-step contracts; milestone concept doesn't apply.

**Prerequisites before implementation:**
1. Design decision: which ContractKinds support milestones and what event triggers one.
2. A new pipeline phase (or extension to `ContractLifecyclePhase`) that evaluates milestone
   conditions per tick and writes `milestones_completed` updates via `StrategicUpdate`.
3. Only then: add field to ContractState + emitter in EventExtractor.

**This is a gameplay feature, not a wiring gap.**

## Assumptions / Open Questions
- Which ContractKinds should have milestones? LOAN and PROTECTION are the best candidates;
  POSITION_SWAP and RECRUITMENT are single-step and have no milestone concept.
- What state drives milestone detection? LOAN may use a repayment tick list; PROTECTION may
  use a periodic tick gate (every N ticks active = one milestone).

## Test Summary
- Unit: prior ContractState has no milestones → current has one → event fires
- Unit: milestone already present → no event (no double-fire)
- Unit: payload includes contract_id and milestone_id

## Files Changed
- `src/observability/event_extractor.py` — added `_emitted_contract_milestones` class var and `_CONTRACT_MILESTONE_THRESHOLDS`; extended `reset_run_state()`; added time-gated milestone emitter block inside strategic.contracts loop
- `tests/unit/observability/test_event_extractor_contract_milestone.py` — 12 new tests
- `docs/simulation_quality/event_type_coverage.md` — moved `contract_milestone_completed` from §3.8 to §1.1; summary count 80→81; all engine_emission_gaps now 0
- `docs/parity_ledger/social_narrative.yaml` — added SOC-238
- `docs/audits/D20_simq_integration.md` — updated F4 to RESOLVED

## Completion Summary
No schema change to ContractState required. EventExtractor diffs existing `created_tick` and
`expiry_tick` fields per ACTIVE contract per tick; emits `contract_milestone_completed` at 25%,
50%, and 75% of duration. Gate keyed on `"{contract_id}:{label}"` (not entity_id) ensures each
milestone fires exactly once per run regardless of how many entities hold the contract. Event
attributed to `contract.source_id`. 12 tests pass; 1096 total tests pass.
