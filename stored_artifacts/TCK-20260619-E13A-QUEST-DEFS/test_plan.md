# Test Plan — TCK-20260619-E13A-QUEST-DEFS

## Scope

Pure YAML content authoring. No code changes. Tests verify:
1. Repository loads all modules without validation errors
2. Quest count meets the ≥34 threshold
3. E2E smoke tests (compositions) still pass

## Test Commands

### 1. Repository load validation
```bash
python3 -c "from src.worldmodules.repository import WorldModuleRepository; r = WorldModuleRepository(); r.load_all(); print('OK')"
```
Expected: prints `OK`, no exceptions.

### 2. Quest count check
```bash
grep -r "type:" data/content/world_modules/ | grep -E "escort|hunt|fetch|explore|defend|investigate" | wc -l
```
Expected: ≥ 34

### 3. E2E smoke tests
```bash
pytest tests/integration/worldassembly/test_e2e_smoke.py -x -v
```
Expected: all pass.

### 4. Quest definition unit tests (regression)
```bash
pytest tests/unit/worldbuilding/test_quest_definition.py -v
```
Expected: all pass (schema not changed, so these must remain green).

## Coverage

| Scenario | Check |
|---|---|
| Repository loads all 15 modules | Load test above |
| Each added quest has valid type | Schema validation at load |
| Each quest has non-empty id | Schema validation (min_length=1) |
| Quest count ≥ 34 | grep count check |
| No composition breakage | E2E smoke test |
| Schema regression | unit test suite |
