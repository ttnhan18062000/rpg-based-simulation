---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CONSUMERS-CORE
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260903-MONITORING-DATA-CONSUMERS-CORE

## Title
Migrate `tools/agent-monitoring/` core readers (`build_index.py`, `generate_retro.py`,
`manifest.py`, `seq_offset.py`, `weight_sensitivity_check.py`, `retro_nudge_hook.py`,
`done_ticket_monitoring_coverage.py`, `validate.py`, `query.py`) to the unified per-week
`agent-monitoring/data/` layout, fixing `weight_sensitivity_check.py`'s live `TOOLS_FILE`
ground-truth bug

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Child 3 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`. Confirmed hardcoded single-path constants
via direct grep this session (line numbers as of this scoping session, reconfirm at implementation):

- `generate_retro.py`: `RUNS_FILE` (line 53), `EVENTS_FILE` (line 54) — still single-file.
  `DEFAULT_TOOLS_FILE` (line 57) already dir-aware for the prior epic's `tools/` shard directory only
  — must be repointed to the new `agent-monitoring/data/` layout, generalized across all 3 sources.
- `build_index.py`: `DEFAULT_RUNS_FILE` (line 42), `DEFAULT_EVENTS_FILE` (line 43) — still
  single-file. `DEFAULT_TOOLS_FILE` (line 44) — same repoint/generalize as above.
- `seq_offset.py`: `EVENTS_FILE` (line 27) — still single-file.
- `retro_nudge_hook.py`: `RUNS_FILE` (line 18) — still single-file.
- `weight_sensitivity_check.py`: `TOOLS_FILE` (line 29) — **confirmed to hardcode the literal,
  now-permanently-empty legacy path `agent-monitoring/tools.jsonl`, the same live bug class as
  `record_events.py`'s (fixed in child 1) — this file's tools-source read has been silently reading
  nothing since the prior epic's `git rm`.** `EVENTS_FILE` (line 30) — still single-file.
- `done_ticket_monitoring_coverage.py`: reads `runs.jsonl` directly per its own doc comments (lines
  62, 70, 94) — exact literal path constant to confirm at implementation time (not fully resolved by
  this session's grep).
- `validate.py`/`query.py`: the prior epic confirmed these are largely SQLite-index consumers with no
  direct `tools.jsonl` path constant (only `DEFAULT_DB_PATH`); `validate.py` additionally has a
  dir-aware `load_jsonl()` the prior epic's child 3 added for the `tools` source specifically. Neither
  file's `runs.jsonl`/`events.jsonl` surface has ever been checked, since the prior epic was tools-
  only — must be reconfirmed here, not assumed unaffected.

## Scope
- Generalize each hardcoded single-path constant (`RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_RUNS_FILE`/
  `DEFAULT_EVENTS_FILE` etc.) in `build_index.py`, `generate_retro.py`, `seq_offset.py`,
  `retro_nudge_hook.py`, `weight_sensitivity_check.py`, `done_ticket_monitoring_coverage.py` to glob
  across `agent-monitoring/data/*/<source>.jsonl` (all week folders, sorted by ISO week,
  concatenated), reusing/extending the dual-mode directory-glob-or-literal-file `load_jsonl()`
  pattern `generate_retro.py`/`validate.py` already have for the `tools` source, generalized to all
  3 sources for every consumer that reads more than one.
- Extend `generate_retro.py`'s `_index_is_stale()` / `_source_mtime()` helper (already built by the
  prior epic for the `tools` source) so `runs` and `events` staleness also compares against the
  newest week folder's mtime for that source, not one file's.
- Extend `build_index.py`'s table-build routine so `monitoring.db`'s `runs`/`events` tables are built
  from the full multi-week glob, same as `tools` already is.
- **Fix `weight_sensitivity_check.py`'s `TOOLS_FILE` bug** as an explicit, dedicated line item — its
  tools-source read must glob `agent-monitoring/data/*/tools.jsonl`, matching child 1's fix to the
  same bug class in `record_events.py`.
- Confirm and fix (or document as a confirmed no-op) `validate.py`'s and `query.py`'s
  `runs.jsonl`/`events.jsonl` surface.
- Confirm `done_ticket_monitoring_coverage.py`'s exact `runs.jsonl` reference and generalize it the
  same way as the other single-source consumers.

## Out of Scope
- `tools/gate_checks/done_checker_static.py` and `src/api/agent_ops_dashboard/ingest.py` — those are
  child 4, kept separate for independent, more careful review of production-API-facing/gate-blocking
  code.
- `tools/agent_replay_codex/monitoring_shards.py` and the codex subsystem — child 5.
- Referential-integrity verification — child 6.
- Any change to `build_index.py`'s table schema, or to `_resolve_status()`/`_is_legacy_event()`/any
  other centralized normalization logic — only the file-resolution layer changes.
- The write path — already done by child 1 (hard prerequisite via child 2).

## Acceptance Criteria
- [x] `python3 tools/agent-monitoring/build_index.py` (`make agent-monitoring-index`) builds
      `monitoring.db`'s `runs`/`events`/`tools` tables from all week folders under
      `agent-monitoring/data/`, with row counts equal to the totals across all weeks, for all 3
      tables.
- [x] A test simulates 2+ week folders under a temp `agent-monitoring/data/`-shaped directory and
      confirms `build_index.py` reads and includes records from all of them, for all 3 sources.
- [x] `generate_retro.py`'s on-demand build path and staleness check correctly detect a newly
      appended row in ANY week folder's ANY of the 3 files as making the index stale.
- [x] **Regression test proving `weight_sensitivity_check.py`'s bug is fixed**: a test with real
      multi-week seeded `tools`/`events` data asserts the script's tools-source-derived weight
      computation is nonzero/correct, not silently empty.
- [x] `seq_offset.py`, `retro_nudge_hook.py`, `done_ticket_monitoring_coverage.py` each correctly read
      the union of week folders for the source(s) they consume.
- [x] `query.py`'s existing test suite passes unmodified (or with only confirmed-necessary changes,
      documented in Implementation Notes).
- [x] `validate.py`'s drift-report functions produce identical results on the post-migration corpus as
      pre-migration, for a fixed historical time window (regression check).

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY (child 1)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — hard prerequisite: this ticket's tests need real
  multi-week files on disk)
- TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD (child 4 — independent, file-disjoint,
  parallelizable with this ticket once child 2 lands)
- TCK-20260902-MONITORING-SHARD-CONSUMERS — the prior epic's tools-only consumer migration this
  ticket extends to `runs`/`events` and generalizes across all 3 sources.

## Related Docs
- `docs/agent-monitoring/schema.md`, `docs/agent-monitoring/README.md` (staleness-check description,
  Navigation table — broader consumer-facing doc language deferred to child 7 per the prior epic's
  own child-1/child-3 split, but confirm no accuracy gap is left dangling by this ticket's own
  functional change).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/` — the dual-mode
  directory-glob-or-literal-file pattern and multi-shard mtime staleness-check design this ticket
  generalizes from `tools`-only to all 3 sources.

## Related Code Areas
- `tools/agent-monitoring/build_index.py`
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent-monitoring/manifest.py`
- `tools/agent-monitoring/seq_offset.py`
- `tools/agent-monitoring/weight_sensitivity_check.py`
- `tools/agent-monitoring/retro_nudge_hook.py`
- `tools/agent-monitoring/done_ticket_monitoring_coverage.py`
- `tools/agent-monitoring/validate.py`
- `tools/agent-monitoring/query.py`
- `tools/agent-monitoring/legacy_reader.py` (I/O-free helper library used only by `manifest.py`/
  `generate_retro.py` — no independent read path of its own, but its test file below reads the real
  corpus directly and is affected the same way)
- **3 test files, confirmed RED as of child 2's landing, must be fixed as part of THIS ticket's own
  Definition of Done, not silently rediscovered**: `tests/tools/test_agent_monitoring_manifest.py`
  (4 failures), `tests/tools/test_done_ticket_monitoring_coverage.py` (1 failure),
  `tests/tools/test_agent_monitoring_legacy_reader.py` (2 failures) — all 7 fail with
  `FileNotFoundError`/silent-empty-read against the now-`git rm`'d `agent-monitoring/runs.jsonl`/
  `events.jsonl`, independently verified (not just self-reported) by child 2's Test-phase agent.
  This was explicitly deferred by child 2 as out-of-scope (matching the already-accepted
  `agent_ops_dashboard/ingest.py` gap), on the understanding that fixing `manifest.py`/
  `done_ticket_monitoring_coverage.py`'s read paths here — this ticket's own core scope — will
  naturally fix most of these; explicitly confirm all 7 pass again before this ticket closes, do not
  assume they're covered incidentally without checking.

## Assumptions / Open Questions
- Assumes child 2 (migration) has landed — real, complete week-folder data exists on disk.
- `done_ticket_monitoring_coverage.py`'s exact `runs.jsonl` path constant was not fully pinned down by
  this session's grep (only doc-comment references were found) — the investigator must confirm the
  real constant/read site at implementation time before planning the fix.
- `query.py`'s/`validate.py`'s exact `runs.jsonl`/`events.jsonl` direct-read scope (vs. pure
  index-consumption) needs re-confirmation with real evidence at implementation time, same caveat the
  prior epic's consumer-migration ticket carried for the `tools` source.
- `layer: observability` matches this repo's established pattern.

## Implementation Notes

Implemented all 15 steps of `staging_artifacts/TCK-20260903-MONITORING-DATA-CONSUMERS-CORE/plan.md`
in order, ratifying investigation's Option B design.

- **Step 1** (`validate.py`): `load_jsonl(path)` simplified to literal-single-file-only (dir-mode
  branch deleted). Added `load_data_glob(data_dir, source)` doing
  `sorted(data_dir.glob(f"*/{source}.jsonl"))`, concatenated via `load_jsonl`.
- **Step 2** (`build_index.py`): `DEFAULT_RUNS_FILE`/`DEFAULT_EVENTS_FILE`/`DEFAULT_TOOLS_FILE` all
  repointed to `Path("agent-monitoring/data")`. Added a private `_load_source(path, source)`
  dispatcher (dir -> `load_data_glob`, file -> `load_jsonl`) and routed `build()` through it.
- **Step 3** (`generate_retro.py`): same 3-constant repoint; local `load_jsonl` simplified
  identically to Step 1; added a local `_load_source`; rewrote `_source_mtime(path, source_name)`
  and `_index_is_stale()` to be source-name-aware (all 3 constants now resolve to the same
  directory, so `path.is_dir()` alone can no longer distinguish sources); fixed
  `_load_runs_and_events()`'s fallback branch and `main()`'s `all_tools = ...` call site (both
  correctly flagged by the plan as needing a real one-line change, not the "zero code change"
  investigation originally assumed).
- **Step 4** (`manifest.py`): `_scan_tools_shards` replaced by source-generic
  `_scan_data_dir_glob(data_dir, source)`; `build_manifest()` and `capture_lines()` rewritten so
  all 3 sources (not just `tools`) glob `agent_monitoring_dir/"data"/*/<source>.jsonl`. Manifest
  shape unchanged: still exactly 3 records, one per source, aggregated across all week folders.
- **Steps 5-6**: rewrote `test_manifest_tools_source_aggregates_all_shards` and
  `test_manifest_tools_source_sha256_is_order_stable_across_shards` to the new
  `data/<week>/tools.jsonl` shape; added
  `test_manifest_aggregates_all_3_sources_across_all_week_folders`.
- **Step 7**: `test_agent_monitoring_legacy_reader.py::_recent_records()` repointed to glob
  `agent-monitoring/data/*/{runs,events}.jsonl`. Deviation: also had to exclude the real
  `unknown-week` folder from this test-only recency heuristic (holds a genuine but
  non-chronologically-orderable legacy record) — see plan.md's Deviations section.
- **Step 8** (`seq_offset.py`): `EVENTS_FILE` repointed; `__main__` now calls
  `load_data_glob(EVENTS_FILE, "events")`. New CLI-subprocess test added.
- **Step 9** (`weight_sensitivity_check.py`, the ticket's named critical bug): `TOOLS_FILE`/
  `EVENTS_FILE` repointed; `_load_tool_rows_and_events()` rewritten to iterate
  `load_data_glob(...)` instead of its own hand-rolled `open()` loop. New cross-week regression
  test proves `n_groups_scored > 0` and nonzero bucket means via the real `main()` CLI path.
- **Step 10** (`retro_nudge_hook.py`, the second silent-zero bug): `RUNS_FILE` repointed;
  `_count_done_since()` rewritten to iterate `load_data_glob(RUNS_FILE, "runs")`, entirely inside
  the existing outer `try/except Exception: pass`. Brand-new test file
  `tests/tools/test_retro_nudge_hook.py` (none existed before) covers cross-week counting and the
  fail-silent contract (malformed line, missing data dir).
- **Step 11** (`done_ticket_monitoring_coverage.py`): despite investigation's "zero code change"
  claim, this required the same real one-line fix as Step 3's corrections — `load_jsonl(RUNS_FILE)`
  would `IsADirectoryError` under the new directory-valued `RUNS_FILE`. Changed the import to
  `from validate import load_data_glob` and the read call to `load_data_glob(RUNS_FILE, "runs")`.
  New cross-week regression test added.
- **Step 12** (`test_build_index.py`): rewrote `TestShardedToolsSource`'s 3 tests to the new
  week-subdirectory shape (root `tmp_path` passed directly as `runs_file`/`events_file`/
  `tools_file`); added `TestUnifiedDataDirSource::test_build_index_2plus_week_folders_all_included`
  covering all 3 tables, not just `tools`.
- **Step 13** (`test_generate_retro.py`): rewrote the 2 flat-shard tests to the new shape; added
  `test_generate_retro_index_is_stale_detects_append_in_any_week_folder_any_source` (AC3, all 3
  sources); fixed the 2 previously-undiscovered RED tests
  (`test_correlation_real_corpus_produces_a_real_number`,
  `test_parity_index_readpath_call_count_matches_real_corpus_state`).
- **Step 14**: updated `docs/agent-monitoring/schema.md`'s staleness-mechanism paragraph and
  `docs/agent-monitoring/README.md`'s Navigation table line, exactly as scoped.
- **Step 15**: appended a third, separately-dated addendum to `INFRA-291` in
  `docs/parity_ledger/infrastructure.yaml` via `tools/parity_ledger_writer.py` (never a raw YAML
  edit) — the 2 prior addenda are byte-unchanged (confirmed by diff).

**Deviations from plan.md** (all recorded in `staging_artifacts/.../plan.md`'s own Deviations
section, added this session):
1. 4 additional real-corpus call sites in `test_generate_retro.py` (not named in Step 3's Verify
   list) also called bare `load_jsonl()` against a now-directory-valued constant and needed the
   same `_load_source()` fix.
2. `test_done_ticket_monitoring_coverage.py` mocks `dtmc.load_jsonl` in 7 places — all renamed to
   `dtmc.load_data_glob` since Step 11 changes what the module imports.
3. `manifest.py`'s test file has a second real-corpus read site, `_content_hash_snapshot()`, not
   named in the plan — rewritten to glob all 3 sources uniformly.
4. `test_agent_monitoring_legacy_reader.py::_recent_records()` needed to exclude the real
   `unknown-week` folder from its own recency-sampling heuristic (production glob reads elsewhere
   still correctly include it).
5. Added `test_validate_drift_reports_identical_pre_and_post_migration_fixed_window` (AC7,
   test_plan item 10, Step 1's own Verify list) — initially missed during the Steps 1-15 pass,
   caught and added on final audit.
6. `manifest.py`'s now-unused `_scan_file()` helper (superseded by `_scan_data_dir_glob()`) was
   left in place rather than deleted — not instructed by the plan, judged out of scope.
7. `test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff`
   was observed to fail intermittently due to a real, concurrent write landing on the live
   corpus's current-week `tools.jsonl` between the test's own pre/post hash snapshots (confirmed
   via an isolated reproduction that `build_manifest()` itself performs zero mutation) — not a
   code defect, consistently green in isolation.

## Test Summary

Ran with `/home/u24desktop/Working/venv/bin/python3 -m pytest` (bare `python3` lacks `pydantic`).

- Full scoped regression surface (`test_build_index.py`, `test_generate_retro.py`,
  `test_agent_monitoring_manifest.py`, `test_agent_monitoring_legacy_reader.py`,
  `test_seq_offset.py`, `test_weight_sensitivity_check.py`, `test_retro_nudge_hook.py`,
  `test_done_ticket_monitoring_coverage.py`, `test_validate_agent_monitoring.py`,
  `test_query.py`): **308 passed, 0 failed** (2 pre-existing/unrelated `SkillStalenessWarning`
  soft-warnings, calendar-driven, not code-driven, not part of this ticket's gate).
- All 9 originally-RED tests confirmed GREEN: 4 in `test_agent_monitoring_manifest.py`, 1 in
  `test_done_ticket_monitoring_coverage.py`, 2 in `test_agent_monitoring_legacy_reader.py`, 2 in
  `test_generate_retro.py` (`test_correlation_real_corpus_produces_a_real_number`,
  `test_parity_index_readpath_call_count_matches_real_corpus_state` — the 2 investigation found
  beyond the ticket's own citation).
- Both critical bugs confirmed fixed with dedicated cross-week regression tests:
  - `weight_sensitivity_check.py`:
    `test_weight_sensitivity_check_real_multi_week_tools_and_events_produce_nonzero_score` — real
    `main()` CLI path over 2 real week folders, asserts `n_groups_scored == 2` (was silently 0)
    and nonzero `baseline_mean`/`candidate_mean`.
  - `retro_nudge_hook.py`:
    `test_retro_nudge_hook_counts_done_runs_across_multiple_week_folders` — `_count_done_since()`
    counts 5 DONE records across 2 week folders (was permanently 0).
- `tests/tools/test_query.py` passes unmodified with **zero edits to `query.py`** — confirmed
  (the file was never touched).
- Manual AC1 sanity check: `python3 tools/agent-monitoring/build_index.py` against the real
  corpus reports `runs: 1388 rows, events: 9018 rows, tools: 185093 rows (3 skipped)` — matches
  `wc -l` totals summed across all 16 real week folders for all 3 sources exactly (185093 + 3
  skipped = 185096 total lines).
- `tests/tools/test_skill_usage_metric.py` (courtesy check, out of scope): 3 real-corpus tests
  still fail — confirmed as the pre-existing, explicitly-flagged (investigation.md Risk #5)
  out-of-scope gap in `skill_usage_metric.py` itself, untouched by this ticket per its Scope
  Guards.

## Files Changed

Production (9 files, matching the ticket's own Related Code Areas minus `query.py`, confirmed
untouched):
- `tools/agent-monitoring/validate.py`
- `tools/agent-monitoring/build_index.py`
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent-monitoring/manifest.py`
- `tools/agent-monitoring/seq_offset.py`
- `tools/agent-monitoring/weight_sensitivity_check.py`
- `tools/agent-monitoring/retro_nudge_hook.py`
- `tools/agent-monitoring/done_ticket_monitoring_coverage.py`

Tests (9 modified, 1 new):
- `tests/tools/test_agent_monitoring_manifest.py`
- `tests/tools/test_agent_monitoring_legacy_reader.py`
- `tests/tools/test_seq_offset.py`
- `tests/tools/test_weight_sensitivity_check.py`
- `tests/tools/test_done_ticket_monitoring_coverage.py`
- `tests/tools/test_build_index.py`
- `tests/tools/test_generate_retro.py`
- `tests/tools/test_validate_agent_monitoring.py`
- `tests/tools/test_retro_nudge_hook.py` (new)

Docs and parity ledger:
- `docs/agent-monitoring/schema.md`
- `docs/agent-monitoring/README.md`
- `docs/parity_ledger/infrastructure.yaml` (via `tools/parity_ledger_writer.py`, third addendum to
  `INFRA-291`)

Staging artifact:
- `staging_artifacts/TCK-20260903-MONITORING-DATA-CONSUMERS-CORE/plan.md` (Deviations section
  appended this run)

Explicitly NOT touched (confirmed): `tools/agent-monitoring/query.py`,
`tools/agent-monitoring/legacy_reader.py`, `tools/agent-monitoring/record_run.py`,
`tools/agent-monitoring/record_events.py`, `tools/agent-monitoring/post_tool_hook.py`,
`tools/agent-monitoring/writer.py`, `tools/agent-monitoring/skill_usage_metric.py`,
`tools/agent-monitoring/retrieval_baseline_metrics.py`,
`tools/agent-monitoring/security_gate_firing_check.py`, `tools/gate_checks/done_checker_static.py`,
`src/api/agent_ops_dashboard/ingest.py`, anything under `tools/agent_replay_codex/` or
`tools/agent_codex_pilot_guardrails/`, `tools/agent-monitoring/verify_referential_integrity.py`.

## Completion Summary

Migrated all 9 in-scope `tools/agent-monitoring/` core readers off the dead
monolithic/flat-shard paths onto the unified per-week `agent-monitoring/data/<ISO-week>/
{runs,events,tools}.jsonl` layout, per investigation's ratified Option B design: `load_jsonl()`
stays literal-single-file-only, a new `load_data_glob(data_dir, source)` in `validate.py` handles
the multi-week glob, and a small `_load_source()` dispatcher (duplicated locally in
`build_index.py`/`generate_retro.py`) preserves every existing literal-file-injection test
unmodified. Fixed both live silent-zero-data bugs named/discovered in scope
(`weight_sensitivity_check.py`'s `TOOLS_FILE`, `retro_nudge_hook.py`'s `RUNS_FILE`) with dedicated
cross-week regression tests proving nonzero, correct output. All 9 originally-RED tests plus 2
investigation found beyond the ticket's own citation are now GREEN; 7 previously-GREEN
flat-shard-shape tests were rewritten to the new week-subdirectory shape; `query.py` required zero
edits and its test suite passes unmodified. Full scoped regression surface: 308/308 passing.

Independently re-verified through the full standard-tier pipeline: Test phase (test-scoper)
independently re-ran 308/308, read both critical-bug regression tests' actual bodies and confirmed
them genuine (real multi-week CLI-path seeding, not mocked shortcuts), confirmed `query.py`
genuinely untouched, confirmed manifest.py's 3-record-per-corpus output shape unchanged, and
confirmed the Option B design via direct diff read. Architecture-Verify (architecture-reviewer):
**APPROVED** — all 9 files' scope boundaries confirmed, every pure function confirmed unchanged,
fail-silent contract in `retro_nudge_hook.py` re-confirmed independently, zero scope creep, 2 minor
cosmetic non-blocking notes only (an unsorted-but-order-invariant glob, dead code left in place per
documented deviation). Verify (done-checker): **READY TO CLOSE**, 13/13 Definition-of-Done
conditions PASS.
