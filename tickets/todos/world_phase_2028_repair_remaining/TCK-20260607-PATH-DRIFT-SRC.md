# TCK-20260607-PATH-DRIFT-SRC

## Title
Fix hardcoded old content paths in src/ and add architecture guard

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Two live source files still hardcode the old `data/world_modules` path that was superseded by
`data/content/world_modules` (via `ContentPathConfig`). Any user or test that has migrated to
the correct path will see silent failures or wrong data.

Additionally, `validator.py` defaults to `data/worlds` as the composition source, which is
the old output directory — not the canonical `data/content/world_compositions`.

No architecture guard prevents re-introduction of the old paths.

## Scope

### Bug 1 — `src/content/validator.py`

Line 88:
```python
mod_repo = WorldModuleRepository("data/world_modules")
```
Line 35 / 98:
```python
def load_all_compositions(worlds_dir: str = "data/worlds") -> ...
compositions = load_all_compositions("data/worlds")
```

Fix:
```python
from src.content.paths import ContentPathConfig
_paths = ContentPathConfig()
mod_repo = WorldModuleRepository(_paths.world_modules_dir)
compositions = load_all_compositions(_paths.world_compositions_dir)
```

### Bug 2 — `src/worldbuilding/cli.py`

Line 171:
```python
mod_repo = WorldModuleRepository("data/world_modules")
```

Fix:
```python
from src.content.paths import ContentPathConfig
mod_repo = WorldModuleRepository(ContentPathConfig().world_modules_dir)
```

### Architecture guard — `tests/architecture/test_no_old_structural_content_paths.py`

Add a test that scans all `.py` files under `src/` for:
- `"data/world_modules"` (hardcoded string)
- `WorldModuleRepository("data/world_modules")` (direct instantiation)
- `"data/worlds"` as a composition/module source (not as a WorldRepository output path)

Allowlist:
- `tests/` files explicitly named `legacy_*` or containing `# legacy fixture`
- Migration documentation files
- `WorldRepository("data/worlds")` — this is the compiled world output repo, not the catalog; it is NOT a forbidden path

## Out of Scope
- Do not rename `data/worlds` for `WorldRepository` (it stores compiled world outputs, not catalog input)
- Do not change `WorldRepository` behavior
- Do not update test files that explicitly test old-path behavior (mark them legacy instead)

## Acceptance Criteria
- [ ] `validator.py` uses `ContentPathConfig().world_modules_dir` and `ContentPathConfig().world_compositions_dir`
- [ ] `worldbuilding/cli.py:171` uses `ContentPathConfig().world_modules_dir`
- [ ] Architecture guard exists at `tests/architecture/test_no_old_structural_content_paths.py`
- [ ] Guard fails when `data/world_modules` appears in non-allowlisted src/ code
- [ ] Guard does NOT fail on `WorldRepository("data/worlds")` (output repo, not catalog)
- [ ] All existing tests pass

## Related Tickets
- TCK-20260607-STRICT-MODE-PRODUCTION (same audit, ContentPathConfig theme)

## Related Docs
- `docs/architecture/` — world repository layout ADR
- `world_phase_20_28_repair_remaining.md` R1.1, R1.2

## Related Code Areas
- `src/content/validator.py:35,88,98`
- `src/worldbuilding/cli.py:171`
- `tests/architecture/`

## Assumptions / Open Questions
- Does `src/lab/cli.py:32` `--worlds-dir default="data/worlds"` refer to WorldRepository output or catalog? — likely output, no change needed.

## Implementation Notes
Hotfix — three targeted line changes + one new test file.

## Test Summary
```
pytest tests/unit/content/test_content_paths.py tests/architecture/test_no_old_structural_content_paths.py -q
```

## Files Changed
- `src/content/validator.py`
- `src/worldbuilding/cli.py`
- `tests/architecture/test_no_old_structural_content_paths.py` (new)

## Completion Summary
(to be filled)
