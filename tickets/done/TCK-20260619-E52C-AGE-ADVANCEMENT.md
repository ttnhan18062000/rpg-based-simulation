---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E52C-AGE-ADVANCEMENT
phase: done
date: 2026-06-20
tags: [demographics, age-advancement, elder, biological-modifier, phase-5]
---

# TCK-20260619-E52C-AGE-ADVANCEMENT

## Title
Epic 5.2C · Entity Age Bracket Advancement + Elder Modifiers

## Status
DONE

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
- `src/domains/demographics/cohort.py` — Added `get_age_bracket()` and `compute_elder_attribute_update()`; updated imports (Optional, AttributeComponent, EntityUpdate)
- `tests/unit/world/test_demographics.py` — Added 6 E52C tests: `test_age_bracket_returns_correct_bracket`, `test_elder_modifier_reduces_combat_effectiveness`, `test_non_elder_returns_none`, `test_elder_knowledge_bonus_positive`, `test_elder_mortality_modifier_reduces_vitality_endurance`, `test_elder_modifier_entity_id_preserved`
- `docs/parity_ledger/world_dynamics.yaml` — Added WORLD-DEMO-003 (bracket classification) and WORLD-DEMO-004 (elder modifiers)

## Completion Summary
Implemented Epic 5.2C. Added `get_age_bracket(age_ticks)` pure function with thresholds (young < 3000, adult 3000–6999, elder ≥ 7000) and `compute_elder_attribute_update()` which returns an `EntityUpdate` carrying an `AttributeUpdate` for elder entities (STR/AGI −30%, VIT/END −50%, WIS/CHA +30%). Both acceptance criteria pass. 51/51 unit tests and 2/2 integration tests pass. Parity ledger updated with WORLD-DEMO-003 and WORLD-DEMO-004.
