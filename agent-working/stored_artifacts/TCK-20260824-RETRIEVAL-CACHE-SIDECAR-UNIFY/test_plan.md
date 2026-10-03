# Test Plan — TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY

## Scoped pytest command

```
pytest tests/tools/test_post_tool_hook.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_retrieval_cache.py tests/tools/test_generate_retro.py tests/tools/test_knowledge_gateway_cache.py -q
```

## New tests

- `test_scoped_sidecar_wins_over_stale_unscoped_when_both_exist`
- `test_no_scoped_file_falls_back_to_unscoped_and_deletes_nothing`

## Modified tests

- `test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration` → renamed
  `test_no_pragma_busy_timeout_or_chmod_introduced_by_level2_migration`; one overly broad clause
  dropped (see plan.md), three substantive checks unchanged.

## Non-regression

- All 7 `TestReadCurrentRunSidecar` cases pass with zero changes.
- All `TestLogCacheAccess`/`TestCacheAccessLogInstrumentation`/`TestLevel2Migrations` (minus the
  one narrowed test above) pass unmodified.

## Results

339 passed (full command above run twice, clean both times).
