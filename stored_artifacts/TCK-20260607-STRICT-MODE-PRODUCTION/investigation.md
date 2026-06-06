# Investigation — TCK-20260607-STRICT-MODE-PRODUCTION

## Finding

`CatalogRepository.load_all(strict=True)` always raises `ValueError` on the real
`data/content/` tree because `os.walk` descends into subdirectories that are not managed
by `CatalogRepository`:

- `data/content/world_modules/*.yaml` — managed by `WorldModuleRepository`
- `data/content/world_compositions/*.yaml` — managed by the composition loader
- `data/content/simulation_scenarios/` — managed by `ScenarioLabOrchestrator`

These paths are not in `registered_paths` (built from `CANONICAL_FAMILIES`), so they
are collected into `ignored_files` and trigger the strict-mode `ValueError`.

## Root Cause (confirmed)

`repository.py` lines 283-292: the walk has no exclusion for non-catalog subdirectories.

## Decision

Add `NON_CATALOG_DIRS: frozenset` at module level. Check `rel_path.split("/")[0]` before
appending to `ignored_files`. This preserves strict mode's intent (no stray YAML inside
catalog namespace) while correctly ignoring directories owned by other loaders.

## Alternative considered

Register world_modules files as CANONICAL_FAMILIES members — rejected because that changes
CatalogRepository's ownership scope and breaks the module/catalog boundary.
