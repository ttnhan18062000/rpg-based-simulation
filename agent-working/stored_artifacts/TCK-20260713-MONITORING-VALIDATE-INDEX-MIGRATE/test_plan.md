---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE
artifact_type: test_plan
tags: [agent-monitoring, data-quality, schema]
---

# Test Plan — TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE

## Regression Surface

All tests below are **unit** tests (no live-repo-data dependency, pure fixture-based, no subprocess) unless noted. Group: agent-monitoring tooling (no arena-combat or engine-integration surface — this ticket touches no `src/` file).

- `tests/tools/test_validate_agent_monitoring.py` — **the primary regression gate (AC2)**. Currently **15** test functions (not 13 — see investigation.md Risk #4 for the count correction), all of which must continue to pass with byte-identical report-string output for the same fixture input:
  - `test_drift_report_counts_null_required_fields`
  - `test_drift_report_frequency_table_non_canonical_phase_and_agent`
  - `test_drift_report_frequency_table_non_canonical_tier`
  - `test_drift_report_skips_events_with_unrecognized_workflow_prefix`
  - `test_drift_report_shows_zero_counts_not_omitted_section_when_clean`
  - `test_drift_report_is_read_only`
  - `test_tool_count_drift_report_no_mismatch_when_counts_agree`
  - `test_tool_count_drift_report_detects_undercounted_mismatch`
  - `test_tool_count_drift_report_detects_overcounted_mismatch`
  - `test_tool_count_drift_report_skips_null_fields`
  - `test_tool_count_drift_report_ignores_tools_rows_without_run_id_or_seq`
  - `test_tool_count_drift_report_is_read_only`
  - `test_multi_invocation_collision_report_detects_duplicate_scope_seq1`
  - `test_multi_invocation_collision_report_is_read_only`
  - `test_canonical_vocabulary_single_sourced`

  Note: all 15 currently call `compute_drift_report(runs, events)` / `compute_tool_count_drift_report(events, tools)` / `compute_multi_invocation_collision_report(events)` **directly as pure functions with in-memory fixture lists** — none of them go through `main()`, `load_jsonl()`, or any file I/O except the two explicit `test_*_is_read_only` tests (which `monkeypatch.chdir(tmp_path)` and assert no `agent-monitoring/` directory is created). **This means the migration must not change these three functions' signatures** (`(runs, events)` / `(events, tools)` / `(events)`, all plain-list-in) — only what feeds them inside `main()` may change. If the migration instead changes these functions themselves to take a `sqlite3.Connection`, all 15 existing tests break and must be rewritten, which would violate AC2's "unmodified behavior" framing. Confirm this constraint explicitly before implementation.

- `tests/tools/test_build_index.py` — must stay green, unmodified. Confirms this ticket does not touch `build_index.py`'s schema (Out of Scope).
- `tests/tools/test_generate_retro.py` — must stay green, unmodified. Confirms no accidental cross-touch into `generate_retro.py` (separate sibling ticket's territory).
- `tests/tools/test_agent_monitoring_legacy_reader.py` — must stay green, unmodified. `legacy_reader.py` imports `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` directly from `validate.py`; if those names are removed or renamed, this breaks (investigation.md Risk #2).
- `tests/tools/test_agent_ops_dashboard_ingest.py` — must stay green, unmodified. `src/api/agent_ops_dashboard/ingest.py` calls `validate.load_jsonl` and `validate._record_is_complete` directly; neither's signature/behavior may change.
- `tests/tools/test_query.py` — must stay green, unmodified (read-only cross-check that the sibling migration's precedent — `open_index`/`load_*_from_index` shape — isn't disturbed; not expected to share code with this ticket, but worth a sanity re-run since both files import from the same `agent-monitoring-index/monitoring.db` schema).

## New Tests Required

Per AC1–AC4. Assumes the recommended fold-in of `compute_multi_invocation_collision_report()` (see investigation.md's Recommendation); if Plan decides to defer it instead, drop the `*_collision_report_uses_index` rows below and keep the function's data source as direct `load_jsonl(EVENTS_FILE)` in `main()`.

1. **`test_main_loads_runs_from_index_not_direct_jsonl`**
   Category: unit / architecture guard
   Verifies: `main()` (or a small refactor exposing a `load_runs(db_path)`-style helper) calls `open_index()` + `load_runs_from_index(conn)` to build the `runs` list fed into `compute_drift_report`, not `load_jsonl(RUNS_FILE)`. Build a throwaway fixture SQLite db via `build_index.py`'s own `_create_schema`/`_ingest_runs` (import, not reimplement — mirrors `test_query.py`'s precedent), monkeypatch `validate.RUNS_FILE`/db path, run, assert output reflects the index's content and that `agent-monitoring/runs.jsonl` was never opened (e.g. via `monkeypatch.chdir(tmp_path)` + asserting no crash/fallback to a nonexistent raw file).
   Location: `tests/tools/test_validate_agent_monitoring.py` (or a new `tests/tools/test_validate_index_migration.py` if the existing file's fixture-only style doesn't fit — prefer extending the existing file for cohesion, matching how `compute_multi_invocation_collision_report`'s own tests were appended to this same file rather than split out).

2. **`test_main_loads_events_from_index_not_direct_jsonl`**
   Category: unit / architecture guard
   Verifies: same as #1, for `events` feeding `compute_drift_report`/`compute_tool_count_drift_report`/(`compute_multi_invocation_collision_report` if folded in).
   Location: same file.

3. **`test_main_loads_tools_from_index_not_direct_jsonl`**
   Category: unit / architecture guard
   Verifies: same as #1, for `tools` feeding `compute_tool_count_drift_report`. Also exercises the **new** `load_tools_from_index(conn)` helper this ticket must add (no precedent exists — `query.py` never read `tools.jsonl`).
   Location: same file.

4. **`test_validate_py_has_no_direct_jsonl_reads`**
   Category: architecture guard
   Verifies: mirrors `test_query.py`'s `test_query_py_has_no_direct_jsonl_reads` exactly — read `validate.py`'s source text, assert the constants `RUNS_FILE`, `EVENTS_FILE`, `TOOLS_FILE` (as direct-file-open targets inside `main()`) are gone/no-longer-referenced for JSONL reads, **while confirming `load_jsonl()` itself is still defined** (must NOT be deleted — `legacy_reader.py`/`ingest.py` depend on it; this is the one place this guard must differ from `query.py`'s stricter "load_jsonl absent entirely" assertion).
   Location: same file.

5. **`test_pre_and_post_migration_drift_report_output_identical`**
   Category: unit / regression-parity (AC2's teeth)
   Verifies: for a fixed fixture corpus (reuse `tests/fixtures/agent_monitoring/shape1..shape6*.jsonl` + the two `events_jsonl_*` fixture files, same corpus `test_query.py`'s parity test used), `compute_drift_report(runs, events)` called on (a) lists loaded via `load_jsonl()` directly and (b) lists loaded via `load_runs_from_index`/`load_events_from_index` off a fixture db built from the same source files, produce byte-identical strings.
   Location: same file (or new `tests/tools/test_validate_index_migration.py`).

6. **`test_pre_and_post_migration_tool_count_drift_report_output_identical`**
   Category: unit / regression-parity
   Verifies: same as #5 for `compute_tool_count_drift_report`, including the `tools` list sourced via the new `load_tools_from_index`.
   Location: same file.

7. **`test_pre_and_post_migration_collision_report_output_identical`** (only if fold-in is accepted)
   Category: unit / regression-parity
   Verifies: same as #5/#6 for `compute_multi_invocation_collision_report`.
   Location: same file.

8. **`test_missing_index_produces_actionable_error`**
   Category: unit / failure mode
   Verifies: running `validate.py`'s `main()` (or its new index-loading helper) against a `--db-path`/default path that doesn't exist produces the same actionable `"...run \`make agent-monitoring-index\` first."`-shaped message and `sys.exit(1)` that `query.py`'s `open_index()` produces — confirms the precedented pattern (investigation.md Risk #3) was actually adopted, not silently skipped or replaced with an unhandled traceback.
   Location: same file.

9. **`test_missing_index_exits_nonzero`**
   Category: unit / failure mode
   Verifies: `pytest.raises(SystemExit)` around the missing-index path, asserting a non-zero code — mirrors `test_query.py`'s equivalent pair.
   Location: same file.

10. **`test_legacy_allowlists_still_importable_from_validate`**
    Category: unit / regression / anti-drift guard
    Verifies: `from validate import LEGACY_COMPLETION_FIELDS, LEGACY_TERMINAL_STATUS_VALUES` still succeeds and both are non-empty — guards against AC3 being over-applied (i.e., someone deleting the names outright, breaking `legacy_reader.py`/`build_index.py`'s imports per investigation.md Risk #2).
    Location: same file, or `tests/tools/test_agent_monitoring_legacy_reader.py` if preferred as the "consumer side" guard.

## Scoped Pytest Commands

```
pytest tests/tools/test_validate_agent_monitoring.py -v
pytest tests/tools/test_build_index.py tests/tools/test_query.py tests/tools/test_generate_retro.py -v
pytest tests/tools/test_agent_monitoring_legacy_reader.py tests/tools/test_agent_ops_dashboard_ingest.py -v
```

Never `pytest tests/` — scope stays within `tests/tools/` (agent-monitoring tooling domain; no `src/`, no engine, no arena-combat surface touched by this ticket).

## Anti-Drift Test Guards

- **Signature-preservation guard**: any test asserting `compute_drift_report(runs, events)` / `compute_tool_count_drift_report(events, tools)` / `compute_multi_invocation_collision_report(events)` still accept plain lists (not a `sqlite3.Connection` or a new required kwarg) — this is implicitly covered by all 15 pre-existing tests continuing to pass unmodified (AC2's own wording), but call it out explicitly in review: if any of the 15 needed a source-code change to keep passing, that's a signal the function signatures changed, which is scope creep beyond "migrate the data source."
- **`load_jsonl()` survival guard** (test #4 above): the single biggest risk of silently breaking `legacy_reader.py`/`ingest.py` is treating this migration as a "delete `load_jsonl` like `query.py` did" copy-paste — `query.py` never shared `load_jsonl` externally; `validate.py`'s copy is a shared dependency for 2 other modules. This guard exists specifically to catch that mistake.
- **Raw-value fidelity guard** (tests #5/#6/#7): catches the `events.workflow`-typed-column-vs-`infer_workflow(run_id)` divergence and any other typed-column shortcut that silently changes output (investigation.md Risk #6) — these are regression-parity tests precisely because "the numbers still look reasonable" is not sufficient; only field-for-field/string-for-string identity against a frozen pre-migration reference proves AC2.
- **Allowlist-survival guard** (test #10): catches AC3 being interpreted too aggressively (full deletion) rather than "reduced to a single reference" — a scope-creep failure mode this ticket's own ambiguous premise (investigation.md Risk #1/#2) makes more likely than usual.
- **Non-gating contract guard**: re-run `test_drift_report_is_read_only`, `test_tool_count_drift_report_is_read_only`, `test_multi_invocation_collision_report_is_read_only` as-is (no changes needed) — they already assert no `agent-monitoring/` directory is created as a side effect; equally, no test in this plan should assert `agent-monitoring-index/` gets auto-created by `validate.py` itself (per Risk #3's recommendation, `validate.py` should mirror `query.py`'s "fail with an actionable message," not silently auto-build the index as a side effect of running `make agent-monitoring-validate`).
