---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-STRICT-MODE-PRODUCTION
artifact_type: plan
tags: [strict, mode, production]
---

# Plan — TCK-20260607-STRICT-MODE-PRODUCTION

## Changes

1. `src/content/repository.py`
   - Add `NON_CATALOG_DIRS: frozenset = frozenset({"world_modules", "world_compositions", "simulation_scenarios"})` after `CANONICAL_FAMILIES`.
   - In the ignored-files walk, skip any `rel_path` whose top-level directory is in `NON_CATALOG_DIRS`.

2. `tests/unit/content/test_content_paths.py`
   - Add `test_strict_load_on_real_content_dir`: calls `load_all(strict=True)` on `data/content/` and asserts `ignored_files == []`.
   - Add `test_non_catalog_dirs_constant_matches_path_config`: asserts `NON_CATALOG_DIRS` matches `ContentPathConfig` directory names.

## No changes needed

- `WorldModuleRepository` — unchanged.
- `CANONICAL_FAMILIES` — unchanged.
- `ContentPathConfig` — unchanged.
