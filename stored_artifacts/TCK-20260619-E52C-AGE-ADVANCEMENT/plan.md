# Plan — TCK-20260619-E52C-AGE-ADVANCEMENT

## Overview
Add age bracket classification and elder stat modifiers to the demographics domain.
Two pure functions in `src/domains/demographics/cohort.py`; tests in `tests/unit/world/test_demographics.py`.

## Changes

### 1. `src/domains/demographics/cohort.py`
Add `# Epic 5.2C` header comment.

Add pure function:
```python
def get_age_bracket(age_ticks: int) -> str:
    """Return age bracket for an entity with the given age_ticks."""
    if age_ticks < 3000:
        return "young"
    if age_ticks < 7000:
        return "adult"
    return "elder"
```

Add pure function:
```python
def compute_elder_attribute_update(
    entity_id: int,
    attrs: "AttributeComponent",
    age_ticks: int,
) -> Optional["EntityUpdate"]:
    """
    Compute elder-tier attribute modifiers for one entity.
    Returns None if entity is not elder (age_ticks < 7000).
    Returns EntityUpdate with AttributeUpdate if entity is elder.

    Modifier mapping (Mechanics Bible §1, Chapter 01):
      combat_effectiveness *= 0.7  → STR and AGI reduced by 30%
      mortality_rate *= 2.0        → VIT and END reduced by 50% (increased mortality pressure)
      knowledge_reputation_weight *= 1.3 → WIS and CHA increased by 30%
    """
```

### 2. `tests/unit/world/test_demographics.py`
Append two test functions (not inside a class, matching ticket AC names):
- `test_age_bracket_returns_correct_bracket` — checks young/adult/elder boundary values
- `test_elder_modifier_reduces_combat_effectiveness` — verifies EntityUpdate with negative STR/AGI delta for elder entity

## Out of scope
- Engine-phase wiring (no pipeline phase modification needed for AC)
- Cohort-level mortality rate mutation (cohort mortality handled in E52A)
- Integration with `DemographicCycleService`

## Acceptance Criteria Mapping
| AC | Test | Pass condition |
|---|---|---|
| `test_age_bracket_returns_correct_bracket` | unit | "young" < 3000, "adult" 3000–6999, "elder" ≥ 7000 |
| `test_elder_modifier_reduces_combat_effectiveness` | unit | EntityUpdate.attributes.strength_delta < 0 for age_ticks=7000 |
| Elder via AttributeUpdate | arch | No direct mutation of frozen EntityState |
