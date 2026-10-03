---
ticket_id: TCK-20260619-E13B-MODULE-TYPES
phase: test_plan
date: 2026-06-20
---

# Test Plan: TCK-20260619-E13B-MODULE-TYPES

## AC Verification

| AC | Test |
|---|---|
| 4 new YAML files exist and load without errors | WorldModuleRepository().load_all() succeeds + len >= 19 |
| `python3 -c "...WorldModuleRepository...load_all()...print('OK')"` passes | Direct CLI check |
| `make world-validate` passes | Run after authoring |
| terrain ≥ 2 from 0, population ≥ 2 from 0 | list_modules_by_type assertions |

## Scoped pytest command

```bash
pytest tests/integration/worldassembly/test_real_content_world_modules.py \
       tests/unit/worldmodules/test_modules.py \
       tests/unit/worldmodules/test_schema_unified.py \
       -x -v
```

## Test Cases

### Load test
- All 4 new modules load via WorldModuleRepository.load_all()
- module_type "terrain" and "population" accepted by schema

### Type distribution
- list_modules_by_type("terrain") returns ≥ 2
- list_modules_by_type("population") returns ≥ 2

### Schema validation
- Each YAML parses to a valid WorldModuleSpec without errors
- No extra/unknown fields (extra="forbid")

### Reference integrity
- factions ref catalog entries (existing test covers this)
- populations ref catalog entries (existing test covers this)
- resources ref catalog entries (existing test covers this)
- buildings ref catalog entries (existing test covers this)

### Normalizer
- WorldModuleAuthoringNormalizer.normalize() succeeds for all 4 new modules
