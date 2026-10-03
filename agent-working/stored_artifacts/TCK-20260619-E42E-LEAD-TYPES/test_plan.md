---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42E-LEAD-TYPES
artifact_type: test_plan
tags: [information-seeking, lead-kind, person-lead, concept-lead]
---

# Test Plan — TCK-20260619-E42E-LEAD-TYPES

## Scope
Unit tests in `tests/unit/cognition/test_information_seeking.py` covering:
1. `LeadKind` enum acceptance (PERSON, CONCEPT, plus existing kinds)
2. PERSON lead routing → INVESTIGATE objective
3. CONCEPT lead routing → ASK_INFORMATION objective
4. No regression on existing leads tests

## New Test Cases

### Class: TestLeadKindEnum

#### test_person_and_concept_lead_types_accepted
- Create `LeadState(kind=LeadKind.PERSON, ...)` and `LeadState(kind=LeadKind.CONCEPT, ...)`
- Assert `lead.kind == "person"` and `lead.kind == "concept"` (str compatibility)
- Assert `isinstance(lead.kind, LeadKind)` for typed construction
- Assert all five LeadKind values are importable and unique

#### test_lead_kind_string_compatibility
- Construct LeadState with `kind="location"` (raw string) — must still work
  (the field is typed but `str, Enum` members compare equal to their string values)
- Assert `LeadState(kind="location").kind == LeadKind.LOCATION` after any coercion,
  OR simply that existing code is unbroken

### Class: TestLeadRoutingSystem

#### test_person_lead_routes_entity_to_provider
- Create entity with a PERSON lead (`subject="42"`, pointing to entity_id 42)
- Call `LeadRoutingSystem.resolve_objective_kind(lead)` 
- Assert result is `(ObjectiveKind.INVESTIGATE, "42")` (navigate to entity_id)

#### test_concept_lead_routes_to_information_provider
- Create entity with a CONCEPT lead (`subject="alchemy_recipe"`)
- Call `LeadRoutingSystem.resolve_objective_kind(lead)`
- Assert result is `(ObjectiveKind.ASK_INFORMATION, "alchemy_recipe")`

#### test_location_lead_routing_unchanged
- LOCATION lead → `(ObjectiveKind.REACH_LOCATION, lead.detail or lead.subject)`
- Ensures no regression

## Regression Tests
Run: `pytest tests/unit/cognition/test_information_seeking.py -x -v`
All existing tests must pass with zero modifications.

Run: `pytest tests/unit/strategic/ -x -v`
Detour, belief, capacity, memory tests — all must pass.

## Acceptance Criteria Coverage
- `test_person_and_concept_lead_types_accepted` ✓
- `test_person_lead_routes_entity_to_provider` ✓  
- All existing lead tests pass (no regression) ✓
