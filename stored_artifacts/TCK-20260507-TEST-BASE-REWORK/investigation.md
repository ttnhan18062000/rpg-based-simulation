# Investigation: Legacy Builder API in Tests

## Findings

- 320 failures + 49 errors all trace to ~25 legacy V2EntityBuilder methods
- Two production source files also affected: `generator.py`, `scenarios.py`
- Each failing test file defines its own local `make_entity`/`create_mock_entity` helper that calls legacy methods
- The shared `tests/helpers/entities.py` already uses the correct V2 API
- No architectural issues — purely a naming/signature migration

## Error Distribution by Domain

| Domain | Files | Failures |
|--------|-------|----------|
| rpg | 20 | ~100 |
| engine | 91 | ~90 |
| social | 11 | ~30 |
| systems | 10 | ~30 |
| world | 19 | ~30 |
| strategic | 5 | ~15 |
| strategy | 5 | ~15 |
| combat | 3 | ~10 |
| town | 9 | ~15 |
| misc | ~10 | ~35 |
