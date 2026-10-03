---
ticket_id: TCK-20260619-E42D-CONTRADICTION
phase: test_plan
date: 2026-06-21
---

# Test Plan: TCK-20260619-E42D-CONTRADICTION

## Acceptance Tests (required by ticket)

### test_belief_contradiction_fires_on_depleted_lead
- File: `tests/unit/cognition/test_information_seeking.py`
- Setup: Entity with a PRECISE lead pointing to a resource node with `remaining_charges=0`. Provider registered.
- Execute: `LeadContradictionSystem.enforce(state, update)`
- Assert:
  - Returned SimulationEvents list contains an event with `event_type="belief_contradiction"`
  - `entity_updates[entity_id].strategic.leads_add_or_update[0].test_outcome == "FAILURE"`
  - `entity_updates[entity_id].strategic.leads_add_or_update[0].failure_count == 1`
  - `information_providers_update[provider_id].reliability_score == original - 0.1`

### test_lead_staleness_decay_reduces_confidence
- File: `tests/unit/cognition/test_information_seeking.py`
- Setup: `KnowledgeFact(certainty=1.0, recorded_tick=0)`
- Execute: `effective_certainty(fact, current_tick=5000)`
- Assert: result < 0.5
  - At tick 5000: `1.0 * max(0.1, 1.0 - 5000 * 0.0001) = 1.0 * max(0.1, 0.5) = 0.5`
  - So at tick 5001+: result < 0.5 ✓
  - Use tick=5001 to guarantee strictly < 0.5

## Additional Tests

### Normal Flow
- `test_contradiction_updates_lead_failure_count` — failure_count increments from 0 to 1
- `test_contradiction_regenerates_unknown_fact` — new UnknownFact with priority=0.7 generated for original subject
- `test_provider_reliability_floor_at_0_1` — reliability never goes below 0.1 even after many contradictions
- `test_alive_lead_no_contradiction` — resource node with remaining_charges > 0 → no contradiction

### Edge Cases
- `test_no_leads_no_contradiction` — entity with no leads → no updates emitted
- `test_staleness_decay_minimum_0_1` — tick >> 10000 → effective_certainty >= 0.1 (floor)
- `test_staleness_decay_at_tick_zero` — current_tick == recorded_tick → effective_certainty == certainty (no decay)

## Scoped Test Run
```bash
pytest tests/unit/cognition/test_information_seeking.py -x -v -k "contradiction or staleness or lead"
```
