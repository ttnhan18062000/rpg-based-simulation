---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-LEAD-CONTRADICTION-WIRING
phase: open
date: 2026-08-24
tags: [information, strategy, cognition]
---

# TCK-20260824-LEAD-CONTRADICTION-WIRING

## Title
Wire Contradiction Detection into the Live Leads System

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The author wants contradiction detection wired into the Leads system via BeliefContradictionService directly, skipping the flag trap. A sibling orphan, LeadContradictionSystem, must be wired in the same ticket, or 3 of 4 lead kinds stay permanently unable to resolve.

## Scope
- Add a `run_phase()` call in `AuthoritativeApplyPipeline.refine()` (`src/engine/pipeline.py`) wiring `LeadContradictionSystem.enforce()` (`src/engine/pipeline_phases/lead_contradiction.py`) as a per-tick state-scan phase
- Add a real production call site for `BeliefContradictionService.detect()` (`src/domains/information/contradiction.py`), invoked when a `claim_failed_search`/`region_danger_seen` observation is processed, applied via a typed `StrategicUpdate`
- Extend `_is_lead_contradicted()` to cover OBJECT/CONCEPT/EVENT `LeadKind` values, not just the current 'resource'/'location'/'person'/'information' string literals (2 of which are not even real `LeadKind` enum values)
- Update `docs/parity_ledger/strategic_cognition.yaml` STRAT-230's `v2_evidence` with a new pipeline-level test

## Out of Scope
- Any change to the broader Nemesis System scope covered by C9
- Correcting other docs beyond STRAT-230 that may have wrongly claimed `LeadContradictionSystem` was already wired, beyond flagging the discrepancy found in this investigation

## Acceptance Criteria
- [ ] A full `pipeline.refine()` tick call (not direct `.enforce()`) on a state with a non-EXHAUSTED lead pointing at a depleted resource produces `belief_contradiction`/`lead_contradiction_resolved` events and the same mutations `LeadContradictionSystem.enforce()` already produces in isolation
- [ ] `BeliefContradictionService.detect()` is invoked from a real production call site when a `claim_failed_search`/`region_danger_seen` observation is processed, applied via a typed `StrategicUpdate`
- [ ] `_is_lead_contradicted()` is extended to cover OBJECT/CONCEPT/EVENT `LeadKind` values
- [ ] STRAT-230's `v2_evidence` is updated with the new pipeline-level test

## Related Tickets
- TCK-20260619-E42D-CONTRADICTION
- TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS
- TCK-20260619-E42-INFO-SEEKING

## Related Docs
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/information/contradiction.py
- src/engine/pipeline_phases/lead_contradiction.py
- src/engine/pipeline.py
- src/core/strategic.py
- src/domains/information/bridge.py

## Assumptions / Open Questions
- No explicit phase-ordering slot for this wiring exists in the M1 epic doc (unlike C11's PP-02/PP-03) -- the insertion point is an open design question
- Two structurally different insertion points are needed (a per-tick `run_phase` slot for `LeadContradictionSystem`, a different observation-event-driven call site for `BeliefContradictionService`) -- cannot be satisfied by one call-site change

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
