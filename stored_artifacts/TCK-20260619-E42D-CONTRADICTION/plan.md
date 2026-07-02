---
ticket_id: TCK-20260619-E42D-CONTRADICTION
phase: plan
date: 2026-06-21
---

# Plan: TCK-20260619-E42D-CONTRADICTION

## Overview

Implement lead contradiction detection as a new pipeline phase `LeadContradictionSystem` and add `effective_certainty()` utility for staleness decay. Two new tests added to existing test file.

## Changes

### 1. `src/core/updates.py`
Add `information_providers_update: Dict[int, InformationProviderState]` field to `StateUpdate`.
Update `is_noop()`, `merge_many()` to handle the new field.

### 2. `src/engine/pipeline_phases/lead_contradiction.py` (new file)
`LeadContradictionSystem` — decision-only pipeline phase.

Signature:
```python
@staticmethod
def enforce(
    state: AuthoritativeState,
    update: StateUpdate,
) -> tuple[StateUpdate, list[SimulationEvent]]:
```

Logic:
For each alive entity, for each non-EXHAUSTED lead:
1. Check lead consistency against world state:
   - `kind == "resource"` or subject maps to a resource node: check `remaining_charges > 0`
   - `kind == "person"` or subject maps to an entity: check `entity.combat.alive`
   - `kind == "faction"` or subject maps to a faction: (skip for now — faction hostility check is future scope)
2. If inconsistent:
   a. Create updated `LeadState(test_outcome="FAILURE", failure_count=lead.failure_count+1, certainty=EXHAUSTED, tested=True)`
   b. Emit `SimulationEvent(event_type="belief_contradiction", event_category="strategy", ...)`
   c. Add `UnknownFact(subject=lead.subject, priority=0.7)` via updated `SelfModelBundle` in `EntityUpdate.self_model_bundle_set`
   d. Decrease provider reliability: `max(0.1, provider.reliability_score - 0.1)` if `lead.source_entity_id` maps to a registered provider
3. Build `StrategicUpdate(leads_add_or_update=[updated_lead])`, `EntityUpdate`, `StateUpdate`, `information_providers_update`
4. Return `(updated_state_update, [events])`

### 3. `src/cognition/knowledge_model.py`
Add `effective_certainty(fact: KnowledgeFact, current_tick: int) -> float` utility function:
```python
DECAY_RATE = 0.0001

def effective_certainty(fact: KnowledgeFact, current_tick: int) -> float:
    elapsed = max(0, current_tick - fact.recorded_tick)
    decay_factor = max(0.1, 1.0 - elapsed * DECAY_RATE)
    return fact.certainty * decay_factor
```

### 4. `tests/unit/cognition/test_information_seeking.py`
Add class `TestLeadContradiction` with:
- `test_belief_contradiction_fires_on_depleted_lead`
- `test_lead_staleness_decay_reduces_confidence`
- Additional tests per test_plan.md

## Architecture Review Checklist
- [x] All durable changes via typed records (StrategicUpdate, StateUpdate)
- [x] KnowledgeFact never mutated (frozen) — decay at read time only
- [x] No raw domain models from APIs
- [x] Deterministic (sorted entity iteration, no randomness)
- [x] SimulationEvents returned separately from StateUpdate (not embedded in it)
- [x] Provider reliability update via `information_providers_update` in StateUpdate

## Order of Implementation
1. Add `information_providers_update` to `StateUpdate` (updates.py)
2. Add `effective_certainty()` to `knowledge_model.py`
3. Create `lead_contradiction.py`
4. Add tests to `test_information_seeking.py`
5. Run tests
