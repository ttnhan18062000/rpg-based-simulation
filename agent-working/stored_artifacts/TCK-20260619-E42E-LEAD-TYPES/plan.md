---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42E-LEAD-TYPES
artifact_type: plan
tags: [information-seeking, lead-kind, person-lead, concept-lead]
---

# Plan — TCK-20260619-E42E-LEAD-TYPES

## Summary
Formalize `LeadKind` as a `str, Enum` in `src/core/strategic.py`, migrate
`LeadState.kind: str` → `LeadState.kind: LeadKind`, and add a pure-read-only
`LeadRoutingSystem` that resolves the correct `ObjectiveKind` + `target` for
PERSON and CONCEPT leads. Wire routing into `DetourSuggestionSystem`.

## Architecture Review
- All durable mutations go through typed `StrategicUpdate` records — no direct
  state writes. `LeadRoutingSystem` is pure decision logic (read-only).
- Determinism: no randomness introduced; entity/lead iteration order unchanged.
- No raw domain models exposed from APIs.
- `LeadKind(str, Enum)` means all existing string comparisons (`== "location"`)
  continue to work — zero regression risk on read sites.

## Steps

### Step 1 — `src/core/strategic.py`
Add `LeadKind(str, Enum)` enum above `LeadState`:
```python
class LeadKind(str, Enum):
    LOCATION = "location"
    OBJECT = "object"
    EVENT = "event"
    PERSON = "person"
    CONCEPT = "concept"
```
Migrate `LeadState.kind: str` → `LeadState.kind: LeadKind`.

### Step 2 — `src/engine/domain/lead_routing.py` (new)
Pure static class `LeadRoutingSystem` with:
```python
@staticmethod
def resolve_objective_kind(lead: LeadState) -> tuple[ObjectiveKind, str]:
    if lead.kind == LeadKind.PERSON:
        return (ObjectiveKind.INVESTIGATE, lead.subject)
    if lead.kind == LeadKind.CONCEPT:
        return (ObjectiveKind.ASK_INFORMATION, lead.subject)
    # LOCATION / OBJECT / EVENT fallthrough
    target = lead.detail if lead.kind == LeadKind.LOCATION and lead.detail else lead.subject
    return (ObjectiveKind.REACH_LOCATION, target)
```

### Step 3 — `src/systems/strategic_systems/detour.py`
Import `LeadKind` and `LeadRoutingSystem`. Update `_infer_objective_kind` to
delegate PERSON/CONCEPT leads through `LeadRoutingSystem.resolve_objective_kind`.
Also update the `target` derivation line (currently hard-codes `lead.kind == "location"`)
to use the routing system for PERSON/CONCEPT leads.

### Step 4 — Tests
Add new test class `TestLeadKindEnum` and `TestLeadRoutingSystem` to
`tests/unit/cognition/test_information_seeking.py`.

### Step 5 — Docs
- Update `docs/simulation/domains/information_contract.md` — add PERSON_LEAD and
  CONCEPT_LEAD sections.
- Update `docs/simulation/domains/belief_and_detour_contract.md` if file exists,
  else note in information_contract.md.
- Add entries STRAT-232 and STRAT-233 to `docs/parity_ledger/strategic_cognition.yaml`.
- Run `make knowledge-index-update`.

## Files Changed
- `src/core/strategic.py` — add LeadKind enum, migrate LeadState.kind type
- `src/engine/domain/lead_routing.py` — new LeadRoutingSystem
- `src/systems/strategic_systems/detour.py` — wire LeadRoutingSystem for PERSON/CONCEPT
- `tests/unit/cognition/test_information_seeking.py` — new test classes
- `docs/simulation/domains/information_contract.md` — PERSON/CONCEPT lead docs
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-232, STRAT-233

## Out of Scope
- Changing existing read sites (str comparison compatibility preserved)
- Changing test helper construction sites (raw strings still work)
- Full navigation/movement routing for PERSON leads (out of scope per ticket)
