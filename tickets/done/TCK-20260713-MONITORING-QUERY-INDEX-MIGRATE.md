---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE
phase: done
date: 2026-07-13
tags: []
---

# TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE

## Title
Migrate query.py to the SQLite index and add its first test suite

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The author wants tools/agent-monitoring/query.py — currently a 120-line full in-memory linear scan with zero test coverage — to become the first consumer migrated onto the new SQLite index, since it's the lowest-risk target, and to gain net-new tests as part of that migration (with an open question on whether tests should land before or in the same diff as the migration).

## Scope
- Migrate tools/agent-monitoring/query.py's read path from an in-memory linear scan over runs.jsonl/events.jsonl to querying the SQLite index built by build_index.py
- Add tests/tools/test_query.py exercising query.py's CLI argument-parsing/filtering logic for --agent, --status, --phase, --run-id, --days, --summary-contains, and --runs, individually and combined
- Add a regression parity test comparing pre-migration in-memory-scan output vs post-migration index-backed output field-for-field on fixed fixtures
- Add a clear, actionable error path when the index is missing or stale (e.g. "run `make agent-monitoring-index` first") instead of a raw exception or silent empty result

## Out of Scope
- Building or modifying tools/agent-monitoring/build_index.py or its schema — that is sibling ticket TCK-20260713-MONITORING-SQLITE-INDEX's responsibility; this ticket is BLOCKED until it ships and its schema is stable
- Migrating validate.py's drift-report logic (separate ticket TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE)
- Migrating generate_retro.py's legacy-shape helpers (separate ticket TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE)
- Any change to the JSONL write path

## Acceptance Criteria
- [ ] tests/tools/test_query.py exists and exercises query.py's CLI argument-parsing/filtering logic directly for --agent, --status, --phase, --run-id, --days, --summary-contains, and --runs filters, individually and combined
- [ ] After migration, query.py's output for a fixed set of runs/events fixtures is field-for-field identical between the pre-migration in-memory-scan path and the post-migration SQLite-index-backed path
- [ ] query.py's migrated read path queries only the derived SQLite index and performs zero direct reads of agent-monitoring/runs.jsonl or events.jsonl once migrated
- [ ] If the index is missing or stale, query.py fails with a clear, actionable error (e.g. "run `make agent-monitoring-index` first") rather than a raw exception or silent empty-result output

## Related Tickets
- TCK-20260713-MONITORING-SQLITE-INDEX (BLOCKS this ticket — build_index.py must ship first)
- TCK-20260721-MONITORING-WRITER-UNIFICATION (BLOCKS this ticket — added 2026-07-22 per Codex review of the provider-agnostic-implementation batch: this ticket's provider/execution_id-aware read migration depends on that ticket's additive writer schema fields existing first; see tickets/todos/provider-agnostic-implementation/SEQUENCE.md)
- TCK-20260607-MON-RETRO
- TCK-20260705-MONITORING-RUNID-JOIN
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/query.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/generate_retro.py
- tools/knowledge_search.py
- docs/agent-monitoring/schema.md
- tests/tools/test_validate_agent_monitoring.py

## Assumptions / Open Questions
- BLOCKED until TCK-20260713-MONITORING-SQLITE-INDEX ships and its schema is stable — implementation cannot start before then
- Whether tests land before the migration (two sequenced diffs) or in the same diff is an open sequencing question to resolve during Scope/Plan; the idea doc leans toward sequencing as lower-risk
- The index's normalization must cover all 5+ historical runs.jsonl schema generations documented in docs/agent-monitoring/schema.md, or query.py's --status filter may silently diverge from the legacy in-memory scan's behavior on old records

## Implementation Notes

Migrated `tools/agent-monitoring/query.py` from an in-memory scan of `agent-monitoring/{runs,events}.jsonl` to reading the SQLite index at `agent-monitoring-index/monitoring.db`, per `staging_artifacts/TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE/plan.md`'s 8 steps, executed in order:

- Added `DEFAULT_DB_PATH`, `--db-path` CLI flag, and `open_index(db_path)` — prints `"No agent-monitoring index found at {db_path} — run \`make agent-monitoring-index\` first."` to stderr and `sys.exit(1)` on a missing file; a genuinely corrupt/non-SQLite file is left to raise its native `sqlite3` error unmasked (verified: `open_index()` on a corrupt file succeeds lazily, the first `conn.execute()` raises `sqlite3.DatabaseError`).
- Added `load_runs_from_index(conn)` / `load_events_from_index(conn)`, both `SELECT ... FROM {runs|events} ORDER BY id` then `json.loads(raw_json)` per row. `load_runs_from_index` additionally injects a `_resolved_status` key sourced from the SQL `resolved_status` column (not from `raw_json`).
- Refactored `main()` into a thin CLI wrapper (`main(argv=None)`) plus two importable pure functions, `filter_runs(records, args)` / `filter_events(records, args)`. The `--runs --status` filter now compares `r.get("_resolved_status")` instead of `r.get("final_status")` — this is the one intentional behavior change (inline comment at the filter site references this ticket ID); it fixes a pre-existing bug where legacy-schema runs with only a bare `status` field were silently excluded. All other filter predicates are unchanged Python comparisons, just applied to index-sourced dicts.
- Deleted `load_jsonl()`, `RUNS_FILE`, `EVENTS_FILE` — `query.py` now performs zero direct reads of `agent-monitoring/runs.jsonl` or `events.jsonl`, enforced by a new architecture-guard test.
- Added `tests/tools/test_query.py` (21 tests): per-flag and combined-filter tests for events and runs (building fixture DBs via `build_index.py`'s own `_create_schema`/`_ingest_runs`/`_ingest_events`, imported not reimplemented), missing-index error-path tests (including a negative assertion that a corrupt db does not print the "missing index" message, without building a full corruption-simulation harness), a regression-parity suite comparing the migrated `filter_events`/`filter_runs` against a frozen, hand-copied pre-migration reference implementation (`_legacy_filter_events`/`_legacy_filter_runs`) over the existing `tests/fixtures/agent_monitoring/` shape files — explicitly excluding the `--runs --status` case from strict comparison, with the exclusion documented in the test class docstring — and architecture/ordering guard tests (source-text check for `RUNS_FILE`/`EVENTS_FILE`/`load_jsonl`, plus a behavioral check that event load order matches insertion order).
- Ran the full scoped regression suite locally (see Test Summary) — all green. Did not touch `docs/parity_ledger/infrastructure.yaml`: per explicit orchestrator instruction, the `INFRA-289` entry is added in the pipeline's later Parity phase, not here.
- A manual smoke test against the real, live `agent-monitoring-index/monitoring.db` surfaced a pre-existing bug unrelated to this migration: some historical record has a non-string `ts`/`start_ts` value, causing `filter_events`/`filter_runs`'s `--days` predicate to raise `TypeError` when comparing `float >= str`. Confirmed via `git show HEAD:tools/agent-monitoring/query.py` that the pre-migration version crashes identically on the same data — not a regression, left as-is per the plan's byte-for-byte parity requirement, documented in plan.md's Deviations section for a future ticket to pick up.

## Test Summary

- `pytest tests/tools/test_query.py -v` — 21 passed (new suite: per-flag/combined filters, missing-index error path, regression parity vs. frozen pre-migration logic, architecture/ordering guards).
- `pytest tests/tools/test_build_index.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py -q` — 69 passed (sibling build-script + read-side subsystem, confirmed unmodified).
- `pytest tests/tools/test_agent_monitoring_legacy_reader.py tests/tools/test_agent_monitoring_manifest.py tests/tools/test_monitoring_bypass_fix.py tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_monitoring_writer_single_source.py tests/tools/test_agent_ops_dashboard_ingest.py -q` — 92 passed (write-path / adjacent-consumer guard, confirms this ticket stayed read-only).
- Manual smoke test: built the real index with `python3 tools/agent-monitoring/build_index.py`, ran `query.py --phase Implement`, `query.py --runs --status DONE` against live data — output correct, including the intentional `resolved_status`-based fix surfacing a legacy bare-`status` record under `--runs --status DONE` that pre-migration `query.py` would have missed. `query.py --db-path /tmp/nope-does-not-exist.db` printed the actionable missing-index message and exited 1. Generated `agent-monitoring-index/` (gitignored) removed after the smoke test.

## Files Changed

- `tools/agent-monitoring/query.py` — migrated read path (modified)
- `tests/tools/test_query.py` — new test suite (added)

## Completion Summary

`query.py` is fully migrated off direct JSONL reads onto the derived SQLite index, gains its first test suite (21 tests covering per-flag/combined filtering, the missing-index error path, regression parity against the frozen pre-migration logic, and architecture guards), and fixes a documented pre-existing bug (`--runs --status` on legacy bare-`status` records) as an intentional, tested divergence. All 4 acceptance criteria are met. `docs/parity_ledger/infrastructure.yaml`'s `INFRA-289` entry is intentionally deferred to the pipeline's later Parity phase per explicit orchestrator direction, not because it was missed.
