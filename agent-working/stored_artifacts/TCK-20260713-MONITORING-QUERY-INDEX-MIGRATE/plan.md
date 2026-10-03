---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE
artifact_type: plan
tags: [agent-monitoring, data-quality, schema]
---

# Implementation Plan — TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE

## Summary

Migrate `tools/agent-monitoring/query.py`'s read path from an in-memory linear scan over
`agent-monitoring/{runs,events}.jsonl` to querying the read-only SQLite index built by
`build_index.py` (`agent-monitoring-index/monitoring.db`), and give it its first test suite.
Filtering strategy is Python-side: `SELECT ... , raw_json FROM {runs|events} ORDER BY id`,
then `json.loads(raw_json)` per row and reuse of the exact same dict-based filter/print
functions `query.py` already has today — this is the lowest-risk path to the field-for-field
parity AC (AC2) because the comparison logic itself doesn't change, only the data source. The
one deliberate behavior change is that `--runs --status` now filters on the SQL `resolved_status`
column instead of re-deriving `record.get("final_status")`, fixing a pre-existing bug where
legacy-schema runs with only a bare `status` field were silently excluded — this divergence is
called out explicitly and excluded from the strict-parity test set. Tests land in the same diff
as the migration (see Anti-Drift Notes for why the "two sequenced diffs" idea-doc lean is not
followed), using a frozen copy of the pre-migration filter logic as the parity oracle. No new
CLI flags are added. `--provider`/`--execution-id`/`--ticket-id` are explicitly out of scope
per the resolved reading of Open Question #1 below.

## Steps

### Step 1 — Add index-path helpers and missing-index error handling
**Files:** `tools/agent-monitoring/query.py`
**Change:**
- Add `DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")` (mirror the constant name/shape from `build_index.py` for consistency, but do not import it — `query.py` must not import `build_index.py`, see Scope Guards).
- Add an `--db-path` argument to the argparse parser (`default=str(DEFAULT_DB_PATH)`) so tests can point at a fixture db without touching the real one.
- Add `open_index(db_path: Path) -> sqlite3.Connection`:
  - If `not db_path.exists()`: print an actionable message to stderr, e.g. `f"No agent-monitoring index found at {db_path} — run \`make agent-monitoring-index\` first."`, then `sys.exit(1)` (or raise a dedicated `IndexMissingError` caught once in `main()` and translated to `sys.exit(1)` — either is fine, but the exit path must be exercised by a test, not just the print).
  - If `db_path.exists()`, `sqlite3.connect(str(db_path))` and return the connection. Do not swallow `sqlite3.OperationalError` from a genuinely corrupt db file here — let it propagate as a raw traceback (Anti-Drift Hazard #6 in investigation.md: don't conflate "missing" with "corrupt").
- Do NOT implement staleness (mtime comparison) in this step — see Step 1 scope note below and Anti-Drift Notes item on AC4 scoping.
**Do NOT touch:** `RUNS_FILE`/`EVENTS_FILE` constants yet (removed in Step 3) — keep them defined through Step 2 so the file stays runnable mid-refactor if needed, but stop referencing them once Step 3 lands.
**Verify:** `test_missing_index_raises_actionable_error`, `test_missing_index_exits_nonzero` (test_plan.md #13, #14).

### Step 2 — Replace `load_jsonl()` calls with SQLite-backed record loading
**Files:** `tools/agent-monitoring/query.py`
**Change:**
- Add `load_runs_from_index(conn) -> list[dict]`: `SELECT raw_json FROM runs ORDER BY id`, then `[json.loads(row[0]) for row in cursor]`. Explicit `ORDER BY id` is required (SQLite gives no ordering guarantee without one; this must match today's JSONL-append order — investigation.md Anti-Drift Hazard #5 / test_plan.md #16).
- Add `load_events_from_index(conn) -> list[dict]`: `SELECT raw_json FROM events ORDER BY id`, same `json.loads` pattern.
- In `main()`, replace `records = load_jsonl(RUNS_FILE)` and `records = load_jsonl(EVENTS_FILE)` with `open_index(Path(args.db_path))` followed by `load_runs_from_index(conn)` / `load_events_from_index(conn)`. Close the connection after loading (`conn.close()`) — no need to keep it open since filtering stays Python-side on the loaded dicts.
- **Fix the `--runs --status` bug as part of this step, not as a side effect discovered later:** change line 98's filter from `r.get("final_status") == args.status` to reading the SQL `resolved_status` column value for that row instead of re-deriving `final_status` from `raw_json`. Concretely: `load_runs_from_index` should return `(resolved_status, raw_dict)` tuples (or a dict with an injected `_resolved_status` key merged from the `resolved_status` SQL column, not from `raw_json`), and the `--status` filter on the runs branch must compare against that column value, not `raw_dict.get("final_status")`. This is the one intentional behavior change in this migration (test_plan.md #9) — document it with an inline comment at the filter site referencing this ticket ID.
- All other filter predicates (`--agent`, `--phase`, `--run-id`, `--summary-contains`, `--days` on events; `--run-id`, `--days` on runs) stay byte-for-byte the same Python comparisons as today, just operating on dicts sourced from `raw_json` instead of `load_jsonl()`.
- `print_events()`/`print_runs()` stay unchanged — they already operate on plain dicts, which is exactly what `json.loads(raw_json)` produces.
**Do NOT touch:** `print_events()`, `print_runs()`, `trunc()`, `cutoff_ts()` function bodies — these are pure formatting/computation helpers with no data-source dependency and are out of scope to touch.
**Verify:** test_plan.md #1–#8, #10 (per-flag and combined-filter tests, all still passing with the new data source); #9 (the `--runs --status` fix, asserted as an intentional divergence).

### Step 3 — Remove direct JSONL reads and add the architecture guard
**Files:** `tools/agent-monitoring/query.py`
**Change:**
- Delete `load_jsonl()`, `RUNS_FILE`, `EVENTS_FILE` module-level constants entirely — nothing in the file should reference `agent-monitoring/runs.jsonl` or `agent-monitoring/events.jsonl` paths anymore (AC3).
- Confirm no residual `Path("agent-monitoring/...")` literal remains anywhere in the file (a plain grep is sufficient self-check before moving on; the durable check is the new test below).
**Do NOT touch:** any file outside `tools/agent-monitoring/query.py`. In particular, `validate.py::load_jsonl()` (a different, already-existing function with the same name in a sibling module) must not be touched or renamed — the two are unrelated despite the name collision.
**Verify:** `test_query_py_has_no_direct_jsonl_reads` (test_plan.md #15) — AST/source-text guard mirroring `test_build_index.py::test_build_index_never_touches_write_path_modules`'s pattern (`tests/tools/test_build_index.py:378-382`): read `query.py`'s source text and assert `"RUNS_FILE"`, `"EVENTS_FILE"`, and `"load_jsonl"` do not appear.

### Step 4 — Write `tests/tools/test_query.py`: per-flag and combined-filter tests
**Files:** `tests/tools/test_query.py` (new file)
**Change:**
- Build fixture data as plain-dict lists (mirror `tests/tools/test_validate_agent_monitoring.py`'s style — no live-repo-data dependency), then build a throwaway SQLite db per test (or per-module fixture) using `build_index.py`'s own `_create_schema`/`_ingest_runs`/`_ingest_events` functions directly (import them — this is exactly the "import, not reimplement" precedent set by `build_index.py` itself importing `_resolve_status`/`_record_is_complete`) so the test fixture db has a schema that's guaranteed to match production, not a hand-rolled duplicate schema that could drift.
- Since `query.py`'s current shape is a single `main()` with no separately importable filter functions, invoke via `subprocess.run([sys.executable, "tools/agent-monitoring/query.py", "--db-path", str(tmp_db), ...], capture_output=True, text=True)` and assert on stdout content, OR (preferred, faster, less brittle) refactor `main()` in Step 2 to accept an optional `argv` list and split filtering into small testable functions (`filter_events(records, args)`, `filter_runs(records, args)`) that tests import directly, with `main()` staying a thin CLI wrapper. **Choose the second approach** — it's a larger but still-narrow change confined to `query.py`'s internal structure (no new files, no behavior change to the CLI surface) and makes tests #1–#10 fast unit tests instead of slow subprocess tests. Apply this refactor as part of Step 2's edit, not as a separate step, since it touches the same functions Step 2 is already rewriting.
- Implement test_plan.md tests #1–#10 (`test_filter_by_agent`, `test_filter_by_status`, `test_filter_by_phase`, `test_filter_by_run_id`, `test_filter_by_days`, `test_filter_by_summary_contains`, `test_runs_flag_queries_runs_table`, `test_combined_agent_status_phase_filters_events`, `test_combined_runs_status_and_days_filter`, `test_combined_run_id_and_summary_contains`). For `test_filter_by_days`, monkeypatch or inject the "now" used by `cutoff_ts()` (do not rely on real `datetime.now()` — test_plan.md #5 flags this explicitly to avoid flakiness).
**Do NOT touch:** `tests/tools/test_build_index.py`, `tests/tools/test_validate_agent_monitoring.py`, `tests/tools/test_generate_retro.py` — these must stay green unmodified (test_plan.md's Regression Surface), used only as read/import sources.
**Verify:** `pytest tests/tools/test_query.py -v` — tests #1–#10 pass.

### Step 5 — Write the missing-index error-path tests
**Files:** `tests/tools/test_query.py`
**Change:** Implement test_plan.md #13 (`test_missing_index_raises_actionable_error`) and #14 (`test_missing_index_exits_nonzero`), pointing `--db-path` at a path under `tmp_path` that is never created. Assert the stderr/stdout message contains both `"agent-monitoring-index"`-shaped guidance and the literal text `"make agent-monitoring-index"`, and assert non-zero exit (via `pytest.raises(SystemExit)` if `main()` is invoked directly, or `subprocess` returncode if invoked as a subprocess).
**Do NOT touch:** the corrupt-db case is explicitly not covered by this ticket's AC4 — do not add a test asserting corrupt-db behavior beyond "it does not print the missing-index message" (a single negative assertion is enough if desired; do not build a corruption-simulation harness, that's speculative scope).
**Verify:** `pytest tests/tools/test_query.py -v -k missing_index` — #13, #14 pass; ties back to Step 1's `open_index()`.
**Depends on:** Step 1.

### Step 6 — Write the regression-parity test (AC2)
**Files:** `tests/tools/test_query.py`
**Change:**
- Add a frozen, private reference implementation of the pre-migration filter logic inside the test file itself (a `_legacy_filter_events(records, args)` / `_legacy_filter_runs(records, args)` pair, hand-copied from the pre-migration `query.py` body captured in this plan's Step 2 description above — i.e., the `final_status`-only comparison on the runs branch, exact-match/substring logic on the events branch). This is the "pinned reference" resolution from the investigation's Open Question #4 — do not use `git show` of a pre-migration SHA (fragile, couples the test to git history); a hand-copied frozen function in the test file is simpler and self-contained.
- Build the fixture corpus from `tests/fixtures/agent_monitoring/`'s existing per-shape `.jsonl` files (`shape1_started_finished_notes.jsonl` through `shape6_type_checker_exception.jsonl`, plus `events_jsonl_reason_code_null.jsonl`/`events_jsonl_tool_call_count_absent.jsonl` for events) — do not invent new fixture files.
- For each of the 7 flags individually, plus at least 2 combined-filter cases, run both the frozen `_legacy_filter_*` function and the migrated (post-Step-2) `filter_events`/`filter_runs` functions against the same fixture corpus and assert identical output — **explicitly excluding** the `--runs --status` case (Step 2's intentional fix) from this comparison, with an inline comment naming the exclusion and pointing at this plan's Step 2 section and test_plan.md #9.
- Add test_plan.md #12: extend the same parity harness with the `shape6_type_checker_exception.jsonl` record (permanently-accepted `resolved_status = NULL` case) and assert the migrated path does not crash and produces the same non-match/match behavior as the frozen reference for that record.
**Do NOT touch:** do not make the exclusion list implicit or broad — per test_plan.md's Anti-Drift Test Guards, keep it to exactly the one documented case (`--runs --status`).
**Verify:** `test_pre_and_post_migration_output_field_for_field_identical` (test_plan.md #11), `test_pre_and_post_migration_parity_includes_type_checker_legacy_shape` (test_plan.md #12).
**Depends on:** Step 2 (needs `filter_events`/`filter_runs` to exist as importable functions).

### Step 7 — Write the architecture/ordering guard tests
**Files:** `tests/tools/test_query.py`
**Change:**
- `test_query_py_has_no_direct_jsonl_reads` (test_plan.md #15): read `tools/agent-monitoring/query.py`'s source text, assert `"RUNS_FILE"`, `"EVENTS_FILE"`, `"load_jsonl"` are all absent.
- `test_query_py_output_ordering_matches_source_order` (test_plan.md #16): build a multi-row fixture db with a known non-alphabetical/non-natural insertion order, run the migrated `load_events_from_index`/`load_runs_from_index` (or the CLI end-to-end), and assert output preserves `id`/insertion order — either by asserting the SQL text contains `ORDER BY` (source-text check, weaker) or by asserting actual row order on a fixture with an intentionally scrambled `run_id`/`agent` sort order (behavioral check, preferred — catches a missing `ORDER BY` even if someone later rewrites the SQL string).
**Do NOT touch:** no changes to `query.py` in this step — purely additive tests against Steps 2–3's output.
**Verify:** test_plan.md #15, #16 pass.
**Depends on:** Steps 2, 3.

### Step 8 — Regression suite confirmation and parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:**
- Run the full scoped regression command set from test_plan.md (`test_build_index.py`, `test_validate_agent_monitoring.py`, `test_generate_retro.py`, plus the write-path/adjacent-consumer guard tests) to confirm nothing outside `query.py`/`test_query.py` regressed.
- Add one new `INFRA-xxx` entry to `docs/parity_ledger/infrastructure.yaml` describing query.py's index-backed read-path guarantee (zero direct JSONL reads post-migration; `--runs --status` now reads `resolved_status`), `status: verified`, `priority: P2`, `test_path: tests/tools/test_query.py`. Per CLAUDE.md's Parity Rule, this must land in the same session as the behavior change.
**Do NOT touch:** any other entry in `infrastructure.yaml`; do not touch `substrate.yaml`/`combat_movement.yaml`/etc. — unrelated subsystems.
**Verify:** scoped pytest commands from test_plan.md all green; `docs/parity_ledger/infrastructure.yaml` has the new entry with a passing `test_path`.
**Depends on:** Steps 1–7.

## Scope Guards

- **Do not modify `tools/agent-monitoring/build_index.py` or its SQLite schema.** If a needed field isn't a typed column, extract it from `raw_json` in Python — never add a column as a workaround.
- **Do not modify `tools/agent-monitoring/validate.py` or `tools/agent-monitoring/generate_retro.py`** beyond what Step 4 already does by importing `_create_schema`/`_ingest_runs`/`_ingest_events` (from `build_index.py`, which itself imports from these modules) for test-fixture-db construction. No behavior changes to either module.
- **Do not change the JSONL write path** — `writer.py`, `post_tool_hook.py`, `record_run.py`, `record_events.py` are untouched. This ticket is 100% read-side.
- **Do not add `--provider`, `--execution-id`, or `--ticket-id` CLI flags.** See Anti-Drift Notes for the full reasoning — the ticket's literal Scope/Acceptance Criteria list exactly 7 flags and none of them are these.
- **Do not implement mtime-based staleness detection for AC4.** Only "index file does not exist" is implemented as the concrete, testable "missing" case per this ticket's AC. A future ticket may add real staleness (comparing db mtime to source JSONL mtimes) — do not build it here speculatively.
- **Do not touch `tests/fixtures/agent_monitoring/`'s existing fixture files.** Reuse them read-only; do not edit or add new per-shape fixture files — the existing set already covers the legacy-schema generations this ticket's parity test needs.
- **Do not touch `src/api/agent_ops_dashboard/ingest.py`** — a separate, independent JSONL-reading consumer (5th consumer per investigation.md), explicitly out of scope and covered only by its own existing regression test (`test_agent_ops_dashboard_ingest.py`) which must stay green and unmodified.

## Dependency Map

- Step 1 (index-open + missing-index handling) — independent, no dependency.
- Step 2 (SQLite-backed loading + `--runs --status` fix + `filter_events`/`filter_runs` extraction) — independent of Step 1's internals but both land in `query.py`; do Step 1 first so `open_index()`/`--db-path` exist for Step 2's `main()` wiring to call.
- Step 3 (remove `load_jsonl`/`RUNS_FILE`/`EVENTS_FILE`) — depends on Step 2 (nothing may still call them).
- Step 4 (per-flag/combined tests) — depends on Step 2 (needs `filter_events`/`filter_runs` as importable functions) and Step 1 (needs `--db-path`/fixture-db wiring).
- Step 5 (missing-index tests) — depends on Step 1.
- Step 6 (parity test) — depends on Step 2.
- Step 7 (architecture/ordering guards) — depends on Steps 2 and 3.
- Step 8 (regression run + parity ledger) — depends on all prior steps.

Recommended execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 (matches the numbering above; each step's code lands before its own tests, and Step 3 closes the AC3 gap before Step 7's guard test can meaningfully pass).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `tests/tools/test_query.py` exists and exercises all 7 flags individually + combined | Steps 4, 6, 7 (file creation across steps) | test_plan.md #1–#10 |
| Pre- vs post-migration output field-for-field identical on fixed fixtures | Steps 2, 6 | test_plan.md #11, #12 |
| Migrated read path queries only SQLite index, zero direct JSONL reads | Steps 2, 3 | test_plan.md #15 |
| Missing/stale index produces a clear, actionable error, not a raw exception or silent empty result | Step 1, 5 (missing-only, see Anti-Drift Notes on "stale" scoping) | test_plan.md #13, #14 |

## Anti-Drift Notes

- **Resolved: no new `--provider`/`--execution-id`/`--ticket-id` flags.** The ticket's own Scope and Acceptance Criteria sections list exactly the 7 pre-existing flags and name no provider/execution-id flag anywhere. Live `runs.jsonl` data has 0/715 records carrying `execution_id` or `provider` (re-verified in investigation.md), and `build_index.py`'s schema has no dedicated columns for these fields. `SEQUENCE.md`'s cross-batch note frames this ticket as consuming WRITER-UNIFICATION's additive fields for a "provider/execution-aware read migration" — this plan interprets that phrase as **tolerance**, not **new surface**: the migrated `query.py` must not crash, misclassify, or silently drop a record just because it carries the new additive `execution_id`/`provider`/`ticket_id` keys (Step 2's `json.loads(raw_json)` approach naturally satisfies this — extra keys in a dict are inert to `.get()`-based filters). No test explicitly exercises "a record with execution_id present" beyond this being implicitly covered by any fixture record with extra unrecognized keys not causing failures — if reviewers want an explicit assertion of this, it is a one-line addition to Step 4, not a new flag. The literal, explicit AC checklist governs scope over the SEQUENCE.md note; adding un-requested flags would be scope creep beyond what was accepted in this ticket's own body.
- **Resolved: Python-side filtering, not SQL `json_extract()`.** Chosen because it keeps the exact same comparison functions pre- and post-migration (only the data-loading call changes), which is what makes the AC2 parity test tractable to write and trust. SQL-side `json_extract()` predicates are not used anywhere in this migration.
- **Resolved: AC4 scoped to "missing" only.** No staleness/mtime mechanism exists in `build_index.py` today (confirmed: no timestamp/version metadata table). This plan implements and tests only the file-not-found case. A follow-on ticket for mtime-based staleness is a reasonable low-risk future enhancement, not part of this plan.
- **Resolved: tests land in the same diff as the migration, not two sequenced diffs.** The idea doc's lean toward sequencing (tests against current code first, then migrate) is not followed here because the regression-parity test (Step 6) requires a frozen reference function regardless of sequencing — freezing it inside the test file achieves the same "before" snapshot without a separate diff, and a single diff is easier to review as one coherent unit for a ticket this narrow.
- **The `--runs --status` behavior change (Step 2) is an intentional, documented divergence, not a bug to silently reintroduce.** Do not "fix" it back to `final_status`-only matching in a later cleanup — that would regress a documented improvement. `test_combined_runs_status_and_days_filter` (test_plan.md #9) guards against this regression specifically.
- **Do not conflate "index missing" with "index corrupt."** `open_index()` (Step 1) only special-cases the not-exists case; a corrupt/permission-denied db must still raise its native `sqlite3` exception unmasked.
- **`validate.py::load_jsonl()` is a different function from the one being deleted from `query.py`.** Do not touch it under the mistaken belief it's the same code being migrated — it's an unrelated, unmodified sibling-module function reused (via `build_index.py`'s own imports) only for Step 4's test-fixture-db construction.
- **Ordering must be explicit (`ORDER BY id`).** SQLite does not guarantee row order without it; a naive `SELECT * FROM events` in Step 2 would pass casual manual testing but flake under CI or larger fixture sets. Step 7's ordering guard exists specifically to catch a future regression here even if the SQL text is rewritten.

## Deviations

- **Step 8's parity-ledger half was deferred to the pipeline's later Parity phase, not done in Implement.** The orchestrating agent's Implement-phase brief explicitly directed: architecture review already confirmed the entry should be added as `INFRA-289` (next free ID after `INFRA-288`, re-checked immediately before assignment in case another in-flight ticket claimed it first) in the Parity phase, not Implement. Implement therefore executed only Step 8's first half (run the full scoped regression suite locally to confirm green) and left `docs/parity_ledger/infrastructure.yaml` untouched — the later Parity phase is responsible for adding the `INFRA-289` entry this plan originally scoped into Step 8.
- **Live-data smoke test surfaced a pre-existing, out-of-scope bug, not a regression.** Manually running the migrated `query.py --days N` against the real `agent-monitoring-index/monitoring.db` raised `TypeError: '>=' not supported between instances of 'float' and 'str'` — some historical event/run record has a non-string `ts`/`start_ts` value. Confirmed via `git show HEAD:tools/agent-monitoring/query.py` that the pre-migration version crashes identically on the same live data with the same traceback. Per this plan's own instruction ("all other filter predicates... stay byte-for-byte the same Python comparisons as today"), this bug was left exactly as-is — fixing it would be undocumented scope creep beyond AC2's parity requirement. Not covered by a new test since it requires a non-string `ts` fixture value outside this ticket's documented legacy-shape corpus; flagging here for a future ticket rather than silently working around it.
- No other deviations. All 8 steps were implemented in the order and shape described above; `filter_events`/`filter_runs` take `(records, args)` exactly as specified, `main(argv=None)` is the thin CLI wrapper Step 4 called for, and the regression-parity exclusion list contains exactly the one documented `--runs --status` case.
