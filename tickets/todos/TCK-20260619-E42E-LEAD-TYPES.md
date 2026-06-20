---
status: open
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42E-LEAD-TYPES
phase: open
date: 2026-06-20
tags: [information-seeking, lead-kind, person-lead, concept-lead, phase-4]
---

# TCK-20260619-E42E-LEAD-TYPES

## Title
Epic 4.2E · PERSON and CONCEPT Lead Types

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`LeadState.kind` is currently a raw string with no formal enum. `PERSON_LEAD` and `CONCEPT_LEAD` types are effectively unsupported (unrouted). This ticket formalizes `LeadKind` as an enum and wires routing for person and concept leads.

**Requires:** TCK-20260619-E42D-CONTRADICTION

## Scope

### 1. Add `LeadKind` enum to `src/core/strategic.py`
```python
class LeadKind(str, Enum):
    LOCATION = "location"
    OBJECT = "object"
    EVENT = "event"
    PERSON = "person"
    CONCEPT = "concept"
```

Migrate `LeadState.kind: str` → `LeadState.kind: LeadKind`. Update all read sites.

### 2. PERSON_LEAD routing

When entity has PERSON_LEAD (seeking a specific entity):
- Route: navigate to last-known position of target entity_id
- On arrival: if entity found → success; if dead/moved → `belief_contradiction`

### 3. CONCEPT_LEAD routing

When entity has CONCEPT_LEAD (seeking domain knowledge, e.g. "alchemy_recipe"):
- Route: navigate to nearest `InformationProvider` whose `knowledge_domains` includes the concept domain
- On arrival: standard paid transaction (E42C logic)

After E42E: update `docs/simulation/domains/belief_and_detour_contract.md` and `docs/simulation/domains/information_contract.md`. Update `docs/parity_ledger/strategic_cognition.yaml`. Run `make knowledge-index-update`.

## Acceptance Criteria
- `test_person_and_concept_lead_types_accepted` passes
- `test_person_lead_routes_entity_to_provider` passes
- All existing lead tests pass (no regression from kind → LeadKind migration)

## Related Tickets
- TCK-20260619-E42-INFO-SEEKING (parent epic)
- TCK-20260619-E42D-CONTRADICTION (required)

## Related Docs
- `docs/simulation/domains/belief_and_detour_contract.md` (update with PERSON_LEAD, CONCEPT_LEAD)
- `docs/simulation/domains/information_contract.md` (update information contract)
- `docs/parity_ledger/strategic_cognition.yaml` (add lead type entries)

## Related Code Areas
- `src/core/strategic.py` (LeadKind enum + LeadState.kind migration)
- Lead routing: find in `src/domains/adventure/` or `src/engine/domain/`

## Test Summary
```bash
pytest tests/unit/cognition/test_information_seeking.py -x -v
pytest tests/integration/scenarios/test_information_seeking.py -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
