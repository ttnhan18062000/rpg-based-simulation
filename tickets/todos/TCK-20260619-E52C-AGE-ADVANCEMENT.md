---
status: open
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E52C-AGE-ADVANCEMENT
phase: open
date: 2026-06-20
tags: [demographics, age-advancement, elder, biological-modifier, phase-5]
---

# TCK-20260619-E52C-AGE-ADVANCEMENT

## Title
Epic 5.2C · Entity Age Bracket Advancement + Elder Modifiers

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`age_ticks` already exists at `src/core/state.py:L143`. This ticket adds bracket determination and elder-tier stat modifiers.

**Requires:** TCK-20260619-E52B-MIGRATION

## Scope

New `get_age_bracket(age_ticks: int) -> str` function in `src/domains/demographics/cohort.py`:
```python
def get_age_bracket(age_ticks: int) -> str:
    if age_ticks < 3000: return "young"
    if age_ticks < 7000: return "adult"
    return "elder"
```

Wire bracket-based modifiers into biological/attribute update phase:
- Elder (`age_ticks ≥ 7000`): `combat_effectiveness *= 0.7`, `mortality_rate *= 2.0`, `knowledge_reputation_weight *= 1.3`
- Apply via `AttributeUpdate` (do NOT directly mutate frozen entity state)

Verify `docs/mechanics/01_entity_anatomy.md` § Biological Pressures for attribute modifier ranges before setting values. Elder knowledge bonus and combat penalty must be within mechanics bible ranges.

## Acceptance Criteria
- `test_age_bracket_returns_correct_bracket` passes
- `test_elder_modifier_reduces_combat_effectiveness` passes
- Elder entity attributes modified via AttributeUpdate (not direct mutation)

## Related Tickets
- TCK-20260619-E52-DEMOGRAPHICS (parent epic)
- TCK-20260619-E52B-MIGRATION (required)
- TCK-20260619-E52D-DENSITY-SIGNAL (blocked on this)

## Related Docs
- `docs/mechanics/01_entity_anatomy.md` § Biological Pressures (verify modifier ranges)

## Related Code Areas
- `src/core/state.py:L143` (age_ticks — already exists, no change needed)
- `src/domains/demographics/cohort.py` (get_age_bracket)
- Biological/attribute update phase in engine

## Test Summary
```bash
pytest tests/unit/world/test_demographics.py::test_age_bracket_returns_correct_bracket -x -v
pytest tests/unit/world/test_demographics.py::test_elder_modifier_reduces_combat_effectiveness -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
