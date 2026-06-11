---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-STRICT-MODE-PRODUCTION
phase: done
date: 2026-06-07
tags: [strict, mode, production]
---

# TCK-20260607-STRICT-MODE-PRODUCTION

## Title
Fix strict=True incompatibility with real data/content/ directory

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`CatalogRepository("data/content").load_all(strict=True)` always raises `ValueError` in production because `world_modules/*.yaml`, `world_compositions/*.yaml`, and any other non-catalog YAML files in `data/content/` are detected by `os.walk` as "ignored active YAML files" — but they are not registered in `CANONICAL_FAMILIES`. Strict mode was tested only against isolated `tmp_path` directories and has never been proven to work on the real content tree.

## Scope

### Root Cause

`repository.py:282-292`:
```python
for root, _, files in os.walk(self.content_dir):
    for file in files:
        if file.endswith((".yaml", ".yml")):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, self.content_dir).replace(os.sep, "/")
            if rel_path not in registered_paths:
                ignored_files.append(rel_path)
```

`registered_paths` contains only catalog family paths like `"foundation/materials.yaml"`. It does NOT include:
- `"world_modules/frontier_village_core.yaml"`
- `"world_compositions/frontier_living_world.yaml"`
- `"simulation_scenarios/"` (empty dir, currently fine)

So running with `strict=True` on the real `data/content` dir always fails immediately.

### Fix Direction

Introduce an **exclusion list** of known non-catalog content directories that are managed by separate loaders (`WorldModuleRepository`, composition loader):

```python
NON_CATALOG_DIRS = {"world_modules", "world_compositions", "simulation_scenarios"}

for root, dirs, files in os.walk(self.content_dir):
    rel_root = os.path.relpath(root, self.content_dir).replace(os.sep, "/")
    top_dir = rel_root.split("/")[0] if rel_root != "." else ""
    if top_dir in NON_CATALOG_DIRS:
        continue  # not catalog-managed; don't report as ignored
    for file in files:
        ...
```

This preserves strict mode's intent (no unregistered YAML in the catalog namespace) while correctly ignoring directories managed by other loaders.

### Required additions

1. Add the exclusion logic to `CatalogRepository.load_all`.
2. Add an integration test: `test_strict_load_on_real_content_dir` that calls `CatalogRepository("data/content").load_all(strict=True)` and asserts it succeeds (or has only expected optional-missing warnings).
3. Update `CatalogLoadReport` docstring or code comment to document the exclusion contract.

## Out of Scope
- Do not register world_modules YAML files as CANONICAL_FAMILIES members.
- Do not move world_modules files to a different directory.
- Do not change the WorldModuleRepository.

## Acceptance Criteria
- [ ] `CatalogRepository("data/content").load_all(strict=True)` succeeds on the real content tree
- [ ] Unknown YAML files in catalog-managed directories (`foundation/`, `living/`, `world/`, etc.) still fail strict mode
- [ ] `NON_CATALOG_DIRS` (or equivalent) is documented in code
- [ ] New integration test `test_strict_load_on_real_content_dir` passes
- [ ] All 173 existing tests still pass

## Related Tickets
- TCK-20260607-VALIDATOR-MATURITY-POLICY (same audit)
- TCK-20260607-FAMILY-KEY-MISMATCH (same audit)

## Related Docs
- world_phase_20_28_repair.md Phase 21 — Task 21.2 strict load report

## Related Stored Artifacts
stored_artifacts/TCK-20260607-STRICT-MODE-PRODUCTION/

## Related Code Areas
- `src/content/repository.py:282-324`
- `tests/unit/content/test_content_paths.py` — existing strict mode tests (all use tmp_path)
- `tests/integration/` — new test location

## Assumptions / Open Questions
- Should `simulation_scenarios/` also be excluded even if it gets YAML files in the future? Yes — it is managed by `ScenarioLabOrchestrator`, not by `CatalogRepository`.
- Should `spawn_tables.yaml` and `defaults.yaml` (optional families) still appear in `missing_optional_files` when absent? Yes — that behavior is correct and unchanged.

## Implementation Notes
This is a 9-phase standard ticket. The investigation is done; the fix is straightforward but needs a design-decision artifact confirming the exclusion list is the right approach.

## Test Summary
- Run `pytest tests/unit/content/ tests/integration/content/ -q` after fix.

## Files Changed
- `src/content/repository.py` — add NON_CATALOG_DIRS exclusion in ignored_files detection
- `tests/integration/content/test_strict_mode_real_catalog.py` — new integration test

## Completion Summary
Done. 169 tests pass.
