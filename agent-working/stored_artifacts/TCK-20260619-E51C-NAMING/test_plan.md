---
status: active
ticket_id: TCK-20260619-E51C-NAMING
artifact_type: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E51C-NAMING

## Test Suite

File: `tests/unit/chronicle/test_chronicle_compiler.py`

| TC | Test name | Covers |
|---|---|---|
| TC-13 | `test_milestone_naming_deterministic` | AC-1: same entry → same name every call |
| TC-14 | `test_known_event_type_templates` | each TEMPLATES key produces correct human name |
| TC-15 | `test_unknown_event_type_falls_back_to_subject` | fallback to raw subject name |
| TC-16 | `test_era_naming_matches_dominant_type` | ERA_NAMES lookup + "Era N" fallback |
| TC-17 | `test_calamity_includes_tick_not_subject` | calamity embeds tick, not subject |
| TC-18 | `test_subject_id_not_integer_fallback` | non-numeric subject_id uses raw string |

## Run Command

```bash
pytest tests/unit/chronicle/test_chronicle_compiler.py -x -v
```

## Success Criteria

- All 18 tests (12 existing + 6 new) pass
- No randomness in output — same inputs always produce same output
- `test_milestone_naming_deterministic` (AC-1 required test) passes
