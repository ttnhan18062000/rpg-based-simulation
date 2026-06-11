---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-STRICT-MODE-PRODUCTION
artifact_type: test_plan
tags: [strict, mode, production]
---

# Test Plan — TCK-20260607-STRICT-MODE-PRODUCTION

## Tests added

- `test_strict_load_on_real_content_dir` — regression guard: strict=True on real `data/content/` must not raise and must return `ignored_files == []`.
- `test_non_catalog_dirs_constant_matches_path_config` — structural guard: `NON_CATALOG_DIRS` must match `ContentPathConfig` directory names so they stay in sync.

## Existing tests retained

All existing strict-mode tests in `test_content_paths.py` use `tmp_path` with monkeypatched `CANONICAL_FAMILIES` — these are unchanged and continue to verify strict-mode error paths.

## Run

```
pytest tests/unit/content/test_content_paths.py -q
```
