---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE
artifact_type: test_plan
tags: [agent-monitoring, data-quality, schema]
---

# Test Plan — TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE

## Regression Surface

This ticket rewrites `query.py`'s read path only — it touches no other file's behavior. The regression surface is therefore split between "prove the sibling build-script's contract still holds" (unmodified) and "prove this migration didn't leak into adjacent subsystems."

**Unit — must keep passing unmodified:**
- `tests/tools/test_build_index.py` (17 tests) — `build_index.py` itself is read (imported for its DB schema/path constants, or invoked as a fixture-building step in this ticket's own tests) but never modified. Confirms the schema this ticket depends on hasn't silently drifted mid-ticket.
- `tests/tools/test_validate_agent_monitoring.py` — `validate.py` is read (possibly imported for `_record_is_complete` if the migration needs it) but not modified.
- `tests/tools/test_generate_retro.py` — same reasoning for `generate_retro.py::_resolve_status()`.

**Integration — write-path / adjacent-consumer guard (must stay green, proves this ticket stayed read-only and didn't touch the write path or sibling consumers):**
- `tests/tools/test_agent_monitoring_legacy_reader.py`
- `tests/tools/test_agent_monitoring_manifest.py`
- `tests/tools/test_monitoring_bypass_fix.py`
- `tests/tools/test_monitoring_writer.py`
- `tests/tools/test_monitoring_writer_lockfile_candidate.py`
- `tests/tools/test_monitoring_writer_single_source.py`
- `tests/tools/test_agent_ops_dashboard_ingest.py` — proves `ingest.py`'s independent JSONL-reading path (a 5th consumer, per the sibling investigation) is untouched by this ticket's query.py-only migration.

**Arena-combat:** not applicable — `tools/agent-monitoring/` has no simulation/combat surface.

## New Tests Required

All new tests live in `tests/tools/test_query.py` (net-new file — `query.py` currently has zero coverage). Mirrors `tests/tools/test_validate_agent_monitoring.py`'s style (plain-dict/fixture-file construction, no live-repo-data dependency) plus a CLI-invocation layer since `query.py`'s current shape is a single `main()` with no separately importable filter functions.

**Per-flag filtering (events, the default `main()` path), individually:**
1. `test_filter_by_agent` — unit. Verifies `--agent X` returns only events where `agent == X`.
2. `test_filter_by_status` — unit. Verifies `--status X` returns only events where `status == X` (events, not runs — see #9 for the runs-side status bug fix verification).
3. `test_filter_by_phase` — unit. Verifies `--phase X` returns only matching events.
4. `test_filter_by_run_id` — unit. Verifies `--run-id X` exact match.
5. `test_filter_by_days` — unit. Verifies `--days N` excludes events with `ts` older than the cutoff; needs a fixed/frozen "now" (inject or monkeypatch the cutoff computation, not real `datetime.now()`) so the test isn't time-dependent/flaky.
6. `test_filter_by_summary_contains` — unit. Verifies case-insensitive substring match on `summary`.
7. `test_runs_flag_queries_runs_table` — unit. `--runs` switches to the runs source; verify output shape differs from the events-default path (runs-specific fields: `tier`, `agent_count`, `duration_s`).

**Combined filters:**
8. `test_combined_agent_status_phase_filters_events` — unit. `--agent X --status Y --phase Z` together, all three narrowing (not OR'd).
9. `test_combined_runs_status_and_days_filter` — unit. `--runs --status X --days N` together — this is the specific combination that exercises the legacy `--status`-on-runs bug (Current Behavior: line 98's `final_status`-only check, no `status` fallback). Assert the migrated version correctly matches records where only `resolved_status` (not raw `final_status`) equals `X` — a **behavior improvement over pre-migration `query.py`**, so this test must NOT be part of the AC2 field-for-field regression-parity set (see below) since pre- and post-migration outputs will legitimately differ here. Document this divergence explicitly in the test's docstring so a future reader doesn't mistake it for a parity violation.
10. `test_combined_run_id_and_summary_contains` — unit. `--run-id X --summary-contains Y` together.

**Regression-parity test (AC2):**
11. `test_pre_and_post_migration_output_field_for_field_identical` — integration/regression-parity. Build a fixed fixture corpus (reuse `tests/fixtures/agent_monitoring/`'s existing per-shape `.jsonl` files rather than inventing new ones — see Investigation's Prior Work), run it through both the pre-migration in-memory-scan logic (frozen as a helper — e.g. via `git show <pre-migration-sha>:tools/agent-monitoring/query.py` captured once and pinned as a test fixture module, or a hand-copied frozen reference function, decided at Plan) and the post-migration SQLite-index-backed `query.py`, and assert identical printed output for every one of the 7 flags individually plus at least 2 combined-filter cases — **explicitly excluding** the runs `--status` case (#9 above), which is a known, intentional, documented divergence (bug fix), not a regression.
12. `test_pre_and_post_migration_parity_includes_type_checker_legacy_shape` — regression-parity, sub-case of #11. Fixture set must include the `TCK-20260623-TYPE-CHECKER` 6th legacy shape (`resolved_status` = `NULL`) to confirm the migrated path doesn't crash or diverge on the one permanently-accepted unresolvable-status record (per `docs/agent-monitoring/schema.md`'s Known Limitations).

**Missing/stale index error path (AC4):**
13. `test_missing_index_raises_actionable_error` — unit. Point `query.py` at a `--db-path` (or equivalent override) that doesn't exist; assert a clear, actionable message is printed/raised (e.g. containing `"agent-monitoring-index"` and `"make agent-monitoring-index"`), not a raw `sqlite3.OperationalError` traceback and not a silent empty-result exit.
14. `test_missing_index_exits_nonzero` — unit, paired with #13. Verify the process/function signals failure via a non-zero exit code (or raises), rather than printing the error and continuing as if the query succeeded with zero results — this distinguishes "no matches" from "couldn't query at all," which today's `print_events`/`print_runs` conflate ("No matching events."/"No matching runs.") and must not conflate for the missing-index case.

**Architecture guards (anti-drift):**
15. `test_query_py_has_no_direct_jsonl_reads` — architecture guard. Source-text/AST check (mirrors `test_build_index.py::test_build_index_never_touches_write_path_modules`'s style) asserting `tools/agent-monitoring/query.py` no longer contains `RUNS_FILE`/`EVENTS_FILE` `Path("agent-monitoring/...")` literals or calls its old `load_jsonl()` — enforces AC3 ("zero direct reads... once migrated") as a durable guard, not just a one-time manual check.
16. `test_query_py_output_ordering_matches_source_order` — architecture guard. Explicit `ORDER BY` regression test — SQLite gives no ordering guarantee without one; assert query.py's SQL includes an explicit order clause (or that output for a multi-row fixture comes back in `id`/`seq` order, matching pre-migration JSONL-append order) so ordering can't silently regress into flaky/undefined behavior.

## Scoped Pytest Commands

```bash
# Primary — this ticket's new test suite
pytest tests/tools/test_query.py -v

# Regression — sibling build script + read-side subsystem, confirm unmodified
pytest tests/tools/test_build_index.py tests/tools/test_validate_agent_monitoring.py \
  tests/tools/test_generate_retro.py -q

# Regression — write-path / adjacent-consumer guard, confirm this ticket stayed read-only
pytest tests/tools/test_agent_monitoring_legacy_reader.py tests/tools/test_agent_monitoring_manifest.py \
  tests/tools/test_monitoring_bypass_fix.py tests/tools/test_monitoring_writer.py \
  tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_monitoring_writer_single_source.py \
  tests/tools/test_agent_ops_dashboard_ingest.py -q
```

Never `pytest tests/` — scoped to `tests/tools/` per CLAUDE.md's Testing Rule.

## Anti-Drift Test Guards

- **`test_query_py_has_no_direct_jsonl_reads`** (#15 above) is the primary anti-drift guard for this ticket's core promise (AC3) — without it, a future edit could silently reintroduce a `load_jsonl(EVENTS_FILE)` fallback and nothing would catch it until someone noticed stale results.
- **`test_combined_runs_status_and_days_filter`** (#9) doubles as an anti-drift guard against the opposite mistake: a future "fix" that makes the migrated version bug-for-bug identical to the pre-migration `final_status`-only check (regressing the free improvement `resolved_status` provides) would fail this test.
- **`test_no_incremental_build_flag_exists`-style guard is NOT needed here** — that guard belongs to `build_index.py` (already covered by its own test suite) and is out of scope for `query.py`, which has no build/rebuild concept of its own.
- **`test_query_py_output_ordering_matches_source_order`** (#16) guards against a subtle, easy-to-miss regression class specific to the JSONL→SQL migration: unordered `SELECT` results reading as "basically the same" in small manual smoke tests while silently flaking in CI or on larger fixture sets.
- **A guard for scope-creep on new CLI flags**: if Plan resolves Open Question #1 (Investigation) in favor of adding `--provider`/`--execution-id` flags, add a paired test asserting the *other* interpretation didn't also sneak in (e.g. assert `--ticket-id` was deliberately included or deliberately omitted, matching whatever Plan decided) — prevents an implementer from hedging by adding all three ad hoc without the decision being traceable to a Plan-phase choice.
- **Regression-parity exclusion list must stay explicit and small.** `test_pre_and_post_migration_output_field_for_field_identical` (#11) should maintain an explicit, commented list of any case intentionally excluded from strict parity (currently: the runs `--status` legacy-fallback fix, #9) — an unbounded/implicit exclusion list would let real regressions hide behind "oh, that's probably an intentional difference."
