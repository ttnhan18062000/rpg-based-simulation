# Test Plan — TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION

## Scoped pytest command

```
pytest tests/tools/test_post_tool_hook.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_retrieval_cache.py tests/tools/test_generate_retro.py -q
```

## New tests required

- `test_second_call_in_ad_hoc_session_reads_own_sentinel_not_unscoped_file`
- `test_real_writesidecar_overwrites_earlier_ad_hoc_sentinel`
- `test_ad_hoc_sentinel_pruned_identically_to_any_scoped_file`

## Modified tests

- `test_foreign_scoped_sidecar_not_read_by_different_session` (assertion changed: null, not
  unscoped-fallback value — this is the exact behavior this ticket changes)
- `test_phase_and_agent_included_when_sidecar_present` (fixture moved to scoped path)
- `test_execution_identity_fields_included_when_sidecar_present` (fixture moved to scoped path)
- `test_phase_and_agent_default_to_none_on_partial_sidecar` (fixture moved to scoped path)

## Non-regression

- `test_scoped_sidecar_preferred_over_stale_unscoped_sidecar`,
  `test_two_concurrent_sessions_each_attributed_correctly`,
  `test_stale_scoped_sidecar_pruned`, `test_fresh_scoped_sidecar_not_pruned`,
  `test_concurrent_writers_produce_no_interleaved_or_truncated_lines`,
  `test_single_writer_produces_one_well_formed_line`,
  `test_locking_failure_does_not_propagate` — all pass unmodified.
