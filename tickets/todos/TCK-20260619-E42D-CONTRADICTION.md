---
status: open
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42D-CONTRADICTION
phase: open
date: 2026-06-20
tags: [information-seeking, belief-contradiction, lead-staleness, replanning, phase-4]
---

# TCK-20260619-E42D-CONTRADICTION

## Title
Epic 4.2D · Lead Contradiction + Belief Staleness Decay

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
When an entity tests a lead and finds it wrong (depleted node, dead entity, hostile faction), the simulation currently has no `belief_contradiction` event, provider reputation update, or replanning mechanism. This ticket wires all three.

**Requires:** TCK-20260619-E42C-PAID-TRANSACTION

## Scope

### Lead Test Outcome

When entity arrives at a lead destination:
1. Evaluate consistency: `remaining_charges > 0` (resource node), `entity.is_alive` (person lead), `faction_status != HOSTILE` (faction lead)
2. If inconsistent: emit `SimulationEvent(kind="belief_contradiction", entity_id=..., payload={lead_id, provider_id})`
3. Update: `InformationProviderState.reliability_score -= 0.1` (min 0.1) via `StateUpdate`
4. Mark: `LeadState.test_outcome = "FAILURE"`, `failure_count += 1`
5. Generate: new `UnknownFact(subject=original_subject, priority=0.7)` → triggers new `INFORMATION_SEEKING` project on next cognition tick

### Knowledge Staleness Decay

In `KnowledgeFact` consumer (find where `KnowledgeFact.certainty` is read in belief/cognition):
```python
DECAY_RATE = 0.0001   # certainty halves over 10000 ticks
effective_certainty = fact.certainty * max(0.1, 1.0 - (current_tick - fact.recorded_tick) * DECAY_RATE)
```

Apply effective_certainty at read time — do NOT mutate KnowledgeFact (frozen). Store decay in a derived `effective_certainty` computed property or scoring function.

## Acceptance Criteria
- `test_belief_contradiction_fires_on_depleted_lead` passes
- `test_lead_staleness_decay_reduces_confidence` passes (effective_certainty < 0.5 at tick 5000 for initial certainty 1.0)

## Related Tickets
- TCK-20260619-E42-INFO-SEEKING (parent epic)
- TCK-20260619-E42C-PAID-TRANSACTION (required)
- TCK-20260619-E42E-LEAD-TYPES (blocked on this)

## Related Code Areas
- Lead test outcome: find in cognition or interaction phase where `LeadState.tested` is set
- `src/core/self_model.py` (KnowledgeFact — staleness decay at read time)

## Test Summary
```bash
pytest tests/unit/cognition/test_information_seeking.py::test_belief_contradiction_fires_on_depleted_lead -x -v
pytest tests/unit/cognition/test_information_seeking.py::test_lead_staleness_decay_reduces_confidence -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
