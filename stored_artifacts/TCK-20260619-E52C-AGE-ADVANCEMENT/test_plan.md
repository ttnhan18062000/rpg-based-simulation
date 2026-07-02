# Test Plan — TCK-20260619-E52C-AGE-ADVANCEMENT

## Scope
Unit tests for `get_age_bracket` and `compute_elder_attribute_update`.

## Test file
`tests/unit/world/test_demographics.py` — appended to existing E52A/E52B tests.

## Tests

### test_age_bracket_returns_correct_bracket
- age_ticks=0 → "young"
- age_ticks=2999 → "young"
- age_ticks=3000 → "adult"
- age_ticks=6999 → "adult"
- age_ticks=7000 → "elder"
- age_ticks=99999 → "elder"

### test_elder_modifier_reduces_combat_effectiveness
- Build an elder entity (age_ticks=7000) with strength=10, agility=10
- Call `compute_elder_attribute_update`
- Assert result is not None
- Assert `result.attributes.strength_delta < 0`
- Assert `result.attributes.agility_delta < 0`
- Assert `result.entity_id` matches input

### Additional edge-case tests
- `test_non_elder_returns_none`: age_ticks=6999 → None
- `test_elder_knowledge_bonus_positive`: wisdom_delta > 0, charisma_delta > 0
- `test_bracket_boundary_exact`: test all three exact boundary values (0, 3000, 7000)

## Run command
```bash
cd /home/vboxuser/Work/rpg-based-simulation && pytest tests/unit/world/test_demographics.py -x -v -k "age_bracket or elder_modifier"
```
