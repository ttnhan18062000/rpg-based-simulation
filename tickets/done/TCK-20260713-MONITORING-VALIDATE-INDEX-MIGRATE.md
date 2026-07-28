---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE
phase: done
date: 2026-07-13
tags: []
---

# TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE

## Title
Migrate validate.py's drift-report logic to the SQLite index

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The author wants validate.py's compute_drift_report() and compute_tool_count_drift_report() functions — which currently hand-roll their own LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES allowlists and re-derive groupings by hand — to be migrated to query the shared normalized index instead, consolidating logic that is currently duplicated separately from generate_retro.py's equivalent handling.

## Scope
- Migrate compute_drift_report() and compute_tool_count_drift_report() in tools/agent-monitoring/validate.py to query the shared normalized index (built by build_index.py) instead of hand-rolling LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES groupings from raw runs/events lists
- Remove or reduce the LEGACY_COMPLETION_FIELDS and LEGACY_TERMINAL_STATUS_VALUES allowlists in validate.py to a single reference to the index's shared normalization, eliminating duplication with generate_retro.py's equivalent helpers
- Preserve validate.py's read-only, non-gating exit-code contract through the migration

## Out of Scope
- Building or modifying tools/agent-monitoring/build_index.py or its schema — that is sibling ticket TCK-20260713-MONITORING-SQLITE-INDEX's responsibility; this ticket is BLOCKED until it ships and its schema is stable
- Migrating query.py (separate ticket TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE)
- Migrating generate_retro.py's own independent legacy-shape handling (separate ticket TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE)

## Acceptance Criteria
- [ ] compute_drift_report() and compute_tool_count_drift_report() query the shared normalized index instead of directly re-deriving LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES groupings from raw runs/events lists
- [ ] All 13 existing tests in tests/tools/test_validate_agent_monitoring.py continue to pass unmodified in behavior (same report string output for the same fixture input), proving the migration is output-preserving
- [ ] The LEGACY_COMPLETION_FIELDS and LEGACY_TERMINAL_STATUS_VALUES allowlists in validate.py are either removed entirely or reduced to a single reference to the index's shared normalization
- [ ] validate.py's exit-code contract is unchanged: compute_drift_report/compute_tool_count_drift_report remain purely additive/read-only, and read-only-style assertions still hold when reading from the index

## Related Tickets
- TCK-20260713-MONITORING-SQLITE-INDEX (BLOCKS this ticket — build_index.py must ship first)
- TCK-20260721-MONITORING-WRITER-UNIFICATION (BLOCKS this ticket — added 2026-07-22 per Codex review of the provider-agnostic-implementation batch: this ticket's provider/execution_id-aware read migration depends on that ticket's additive writer schema fields existing first; see tickets/todos/provider-agnostic-implementation/SEQUENCE.md)
- TCK-20260705-MONITORING-RUNID-JOIN
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION (done — added compute_multi_invocation_collision_report() to validate.py after this ticket was filed; see Assumptions/Open Questions)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_derived_index.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/vocabulary.py
- tests/tools/test_validate_agent_monitoring.py
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
- BLOCKED until TCK-20260713-MONITORING-SQLITE-INDEX ships and its schema is stable — implementation cannot start before then
- The exact index schema/API is undecided per the idea doc's Open Questions; this ticket may need to confirm the sibling ticket's index shape before implementation
- The index's normalization must reproduce validate.py's exact legacy-shape handling or risk silently regressing already-fixed false positives from prior hardening tickets
- Scope drift since this ticket was filed (2026-07-13): `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` (done) added a third function to validate.py, `compute_multi_invocation_collision_report()`, alongside the two named in this ticket's Scope. It follows the same read-only/non-gating/hand-rolled-grouping-over-raw-`events.jsonl` shape as `compute_drift_report()`/`compute_tool_count_drift_report()`, so it is a natural candidate for the same index migration — this ticket's own Investigate/Plan phase should decide whether to fold it in (recommended, since leaving one of three sibling functions un-migrated would reintroduce the exact duplication this ticket exists to remove) or explicitly defer it with rationale.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE/plan.md`'s 6 ordered steps (Step 6, the parity ledger update, deferred to the pipeline's later Parity phase as instructed).

- **Step 1** — Added `DEFAULT_DB_PATH`, `open_index()`, `load_runs_from_index()`, `load_events_from_index()`, `load_tools_from_index()` to `tools/agent-monitoring/validate.py`, placed after `LOG_FILE`/`MONITORING_START`, before `LEGACY_COMPLETION_FIELDS`. Written independently (no cross-import from `query.py`), mirroring its `open_index`/`load_events_from_index` shape exactly and its `load_runs_from_index` shape *except* deliberately omitting `_resolved_status` injection (per plan: `compute_drift_report` only reads raw fields, and injecting an unrequested key is out of scope). `load_tools_from_index()` is genuinely new — no precedent existed anywhere in the codebase since `query.py` never reads `tools.jsonl`.
- **Step 2** — Removed `RUNS_FILE`/`EVENTS_FILE`/`TOOLS_FILE` module constants (confirmed via search that nothing outside `validate.py` imports these three names). `main()` now takes `argv=None`, parses a single `--db-path` CLI arg via a new `build_parser()`, and loads `runs`/`events`/`tools` from the SQLite index via `open_index()` + the three `load_*_from_index()` helpers instead of three `load_jsonl()` calls. Everything downstream in `main()` (incomplete-run check, no-events check, working_log cross-check, the three `print(compute_*_report(...))` calls) is byte-for-byte unchanged — same variable names, same order, same control flow. `if __name__ == "__main__": main()` unchanged (argparse defaults handle the no-args CLI case). `Makefile`'s `agent-monitoring-validate` target left untouched, matching `agent-monitoring-query`'s precedent of not auto-building the index.
- **Step 3** — Added 3 regression-parity tests to `tests/tools/test_validate_agent_monitoring.py` (`test_pre_and_post_migration_drift_report_output_identical`, `test_pre_and_post_migration_tool_count_drift_report_output_identical`, `test_pre_and_post_migration_collision_report_output_identical`), built against the same fixture corpus `test_query.py`'s parity test used (`shape1..shape6*.jsonl`, `events_jsonl_*`), plus the two `tools_jsonl_*` fixture files for the tools-dependent reports. All three report functions' bodies are untouched; the tests prove the round-tripped `raw_json` dicts are field-identical to the direct-`load_jsonl()` dicts on this corpus.
- **Step 4** — Added `TestArchitectureGuards` with `test_validate_py_has_no_direct_jsonl_reads` (asserts `RUNS_FILE`/`EVENTS_FILE`/`TOOLS_FILE` are gone from source text, **and** that `load_jsonl` is still defined — the one place this guard differs from `query.py`'s stricter version, since `legacy_reader.py`/`ingest.py` depend on `validate.load_jsonl` surviving) and `test_legacy_allowlists_still_importable_from_validate`.
- **Step 5** — Added `TestMissingIndex` with `test_missing_index_produces_actionable_error`, `test_missing_index_exits_nonzero`, and `test_main_exits_nonzero_when_index_missing`, mirroring `test_query.py`'s `TestMissingIndex` class shape.
- **Step 6** — Deliberately not done in this phase per explicit instruction (parity ledger entry is the pipeline's later Parity phase's responsibility).

**Scope confirmation on `compute_multi_invocation_collision_report()`**: per the ticket's own Assumptions note and the plan's Anti-Drift Notes item 3, this third function (added after this ticket was filed, by `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`) was folded into the migration with **zero dedicated code change** — Step 2's single data-source swap in `main()` automatically migrated it, since it takes the same `events` list as `compute_drift_report`. Only its dedicated parity test (Step 3) was new work.

**AC2/AC3 corrections carried over from the plan** (both explicitly reasoned through in `plan.md`'s Anti-Drift Notes, not silently applied): AC2's ticket text says "13 existing tests" — the file actually had 15 pre-migration (verified by direct count); all 15 continue to pass unmodified, plus 12 new tests were added (27 total). AC3 ("LEGACY_COMPLETION_FIELDS/LEGACY_TERMINAL_STATUS_VALUES reduced to a single reference or removed") is resolved as **satisfied-by-inaction**: neither `compute_drift_report()` nor `compute_tool_count_drift_report()` ever referenced either allowlist — the only consumer is `_record_is_complete()`, which is not named in this ticket's Scope and was left untouched. Deleting the allowlists would break `legacy_reader.py` and `build_index.py`, both of which import them directly from `validate.py`; `validate.py` is already the canonical upstream definer, so there is no "index normalization" to point back at. Guarded by `test_legacy_allowlists_still_importable_from_validate`.

**Known, bounded, out-of-scope-to-fix output divergence found during manual verification against the live corpus** (not caught by the fixture-based test suite, since the specific triggering shape wasn't present in the existing fixture files): `compute_tool_count_drift_report`'s `actual_counts` loop counts any `tools.jsonl` row with a present `run_id`+`seq`, regardless of whether a `tool` field exists. `build_index.py`'s `_ingest_tools()` additionally requires `isinstance(record.get("tool"), str)` before inserting a row, structurally excluding rows that have `run_id`+`seq` but no `tool` field. On the live `agent-monitoring/tools.jsonl` corpus (2026-07-28 snapshot), there is exactly one such record (`run_id=TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP`, `seq=4`), which shifted the live drift report's "Mismatches" count from 487 (direct-JSONL) to 488 (index-sourced) in a manual side-by-side run. This is: (a) non-gating — never changes `validate.py`'s exit code; (b) already visible — `build_index.py` prints a `WARNING: tools.jsonl record skipped` line for this exact record at build time; (c) not fixable within this ticket's scope, since fixing it requires either changing `build_index.py`'s tools-ingestion rule (owned by the sibling `TCK-20260713-MONITORING-SQLITE-INDEX` ticket, explicitly out of scope here) or changing `compute_tool_count_drift_report`'s body to also require a `tool` field (explicitly forbidden — the plan requires the three `compute_*` bodies stay unchanged). Documented and pinned with a new fixture-level test, `test_tools_row_missing_tool_field_is_a_known_bounded_divergence`, in `TestRegressionParity`, so this is a traceable, understood divergence rather than a silent one. Not recorded in `docs/guidelines/intentional_divergences.md` (that registry is scoped to Mechanics Bible/engine-contract behavior; this ticket touches no `src/` simulation code, matching investigation.md's confirmation that no mechanics chapter applies) — flagged here and in the plan's Deviations section instead, and worth a P2 follow-up ticket if a future reader wants byte-identical output guaranteed against every possible off-schema shape rather than the curated fixture corpus.

## Test Summary

`pytest tests/tools/test_validate_agent_monitoring.py -v` — 27 passed (15 pre-existing unmodified + 12 new: 3 `TestMainUsesIndex`, 2 `TestArchitectureGuards`, 4 `TestRegressionParity`, 3 `TestMissingIndex`).

Sibling-suite sanity re-run (test_plan.md's Scoped Pytest Commands): `pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_build_index.py tests/tools/test_query.py tests/tools/test_generate_retro.py tests/tools/test_agent_monitoring_legacy_reader.py tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_monitoring_manifest.py -q` — 171 passed, 0 failed.

Manual end-to-end verification: ran `python3 tools/agent-monitoring/build_index.py` then `python3 tools/agent-monitoring/validate.py` against the live repo corpus (717 runs, 3793 events, 68041/68044 tools rows ingested) — completed successfully, exit 0, non-gating warnings only. Side-by-side comparison of `compute_drift_report`/`compute_tool_count_drift_report`/`compute_multi_invocation_collision_report` output between direct-`load_jsonl()` and index-sourced inputs on the live corpus found `compute_drift_report` and `compute_multi_invocation_collision_report` byte-identical; `compute_tool_count_drift_report` diverged by exactly 1 mismatch count, traced to the known bounded divergence documented above. `agent-monitoring-index/` was removed after manual verification (gitignored, on-demand-build artifact, not meant to be committed).

## Files Changed

- `tools/agent-monitoring/validate.py` — added `open_index`/`load_runs_from_index`/`load_events_from_index`/`load_tools_from_index`/`DEFAULT_DB_PATH`/`build_parser`; removed `RUNS_FILE`/`EVENTS_FILE`/`TOOLS_FILE`; `main()` now takes `argv=None` and sources `runs`/`events`/`tools` from the SQLite index.
- `tests/tools/test_validate_agent_monitoring.py` — added `TestMainUsesIndex`, `TestArchitectureGuards`, `TestRegressionParity`, `TestMissingIndex` (12 new tests); added `build_index`/`pytest`/`json`/`sqlite3` imports.

## Completion Summary

Migrated `validate.py`'s `main()` to source `runs`/`events`/`tools` from the SQLite index (`agent-monitoring-index/monitoring.db`) instead of direct `load_jsonl()` reads on the three source JSONL files, via new `open_index`/`load_runs_from_index`/`load_events_from_index`/`load_tools_from_index` helpers mirroring `query.py`'s precedent (independently written, no cross-import). `compute_drift_report`, `compute_tool_count_drift_report`, and `compute_multi_invocation_collision_report` — all three sibling report functions, with the third folded in per the ticket's own anticipated scope expansion — are unchanged in body/signature and now receive index-sourced lists automatically via `main()`'s single unified data load. `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` are untouched (AC3 resolved as satisfied-by-inaction — neither named function ever used them). `validate.py` now hard-requires the index to exist (actionable stderr + exit 1 if missing, matching `query.py`'s precedent), a deliberate, stated behavior change from its prior zero-precondition standalone operation. 27 tests pass in the primary test file (15 pre-existing unmodified + 12 new); 171 pass across the full sibling-suite sanity check. One known, bounded, non-gating output divergence was found via live-corpus spot-checking (outside the fixture test corpus) and is documented above and pinned with a dedicated test — not blocking, since it's out of this ticket's scope to fix and doesn't affect the exit-code contract. Parity ledger entry (INFRA-290, pending re-verification of the current max ID) deferred to the pipeline's Parity phase per explicit instruction.
