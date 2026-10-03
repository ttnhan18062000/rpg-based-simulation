---
ticket_id: TCK-20260619-E53Ba-DIPLO-STATE
phase: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E53Ba-DIPLO-STATE

## Test File
`tests/unit/faction/test_diplomacy.py`

## Test Cases

### Acceptance Criteria Tests
1. `test_diplomatic_state_enum_round_trip` — DiplomaticState importable, values serialize/deserialize
2. `test_faction_state_diplomatic_relations_apply` — FactionUpdate only updates specified key, preserves others
3. `test_diplomatic_state_str_coercion` — DiplomaticState("ALLIED") == DiplomaticState.ALLIED
4. `test_canonical_dict_emits_string_values` — to_canonical_dict() emits str values not enum objects
5. `test_from_dict_coerces_strings` — from_dict with string values reconstructs typed DiplomaticState

### Regression Tests
6. `test_existing_faction_state_tests_still_pass` — (validated by running test_faction_state.py)
7. `test_scoring_allied_check_uses_enum` — score boost still works after enum migration

## Run Commands
```bash
pytest tests/unit/faction/test_diplomacy.py -x -v
pytest tests/unit/faction/test_faction_state.py -x -v
pytest tests/unit/faction/test_faction_directive_propagation.py -x -v
```
