---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22B-TICK-INDEX
artifact_type: test_plan
tags: [tick-index, decision-trace, observability, testing]
---

# Test Plan — TCK-20260619-E22B-TICK-INDEX

## Regression Surface (existing tests that must pass)

All existing tests in `tests/unit/observability/test_decision_trace.py` (10 tests from E22A):
- `test_decision_trace_written_in_light_mode`
- `test_decision_trace_schema_has_all_score_terms`
- `test_decision_trace_not_written_in_off_mode`
- `test_decision_trace_caps_at_5_routes`
- `test_decision_trace_append_mode`
- `test_decision_trace_selected_flag`
- `test_decision_trace_empty_routes_is_noop`
- `test_set_and_get_active_writer`
- `test_adventure_decision_phase_wires_writer`
- `test_decision_trace_writer_does_not_import_engine_cognition`

## New Tests Required (per AC)

All new tests go into `tests/unit/observability/test_decision_trace.py`.

### AC: test_tick_index_o1_lookup (required by name in AC)
- Create a `decision_trace.jsonl` with 3 ticks × 2 entities = 6 lines
- Call `DecisionTraceIndex.lookup(tick=2)` — assert returns exactly 2 entries (entities for tick 2)
- Verify the lookup did NOT read from offset 0 (mock/patch `open` or check seek position)
- Verify returned entries have correct `tick` and `entity_id` values

### AC: index file exists after run
- After `writer.close()`, assert `decision_trace_index.json` exists alongside `decision_trace.jsonl`
- Verify format: `{"1": <int>, "2": <int>, ...}` (string keys, int values)

### AC: index format correctness
- Build index from known JSONL, verify `{str(tick): byte_offset}` keys/values are correct
- Specifically: offset for tick 1 is 0 (start of file); offset for tick 2 is after the first line

### Additional robustness tests
- `test_tick_index_lookup_missing_tick` — `lookup(tick=99)` returns `[]` (not an error)
- `test_tick_index_rebuild_idempotent` — `rebuild()` twice produces identical index
- `test_tick_index_load_from_disk` — `DecisionTraceIndex._load()` correctly parses saved JSON
  (str→int key conversion)
- `test_tick_index_incremental_vs_rebuild` — Write 3 entries via writer (which updates index
  incrementally), then call `rebuild()` — both produce identical index

## Scoped Pytest Commands

```bash
# Primary AC test (named in ticket)
pytest tests/unit/observability/test_decision_trace.py::test_tick_index_o1_lookup -x -v

# All new tick-index tests
pytest tests/unit/observability/test_decision_trace.py -k "tick_index" -x -v

# Full observability regression
pytest tests/unit/observability/ -x -v -q
```

## Anti-Drift Test Guards

- All `test_decision_trace_*` tests from E22A must remain passing (regression surface).
- `test_tick_index_o1_lookup` must demonstrate byte-seek behavior (not full-scan).
- Index tests must use `tempfile.TemporaryDirectory` — never write to `data/runs/` in tests.
- The `clear_obs_overrides` autouse fixture from E22A must cover all new tests.
