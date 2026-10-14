---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES
artifact_type: test_plan
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES

## Regression Surface
Unit/integration (throwaway git repos under tmp_path), all in `tests/tools/test_main_integrity_report.py`, must keep passing: `test_clean_ref_reports_nothing`, `test_each_planted_defect_is_reported_with_its_ticket_or_path` (event_seq duplicate and duplicate_runs paths via `_load_rows`), `test_working_tree_is_never_read_...`, `test_cli_exits_zero_by_default_...`, `test_since_date_limits_ticket_checks`, the three false-positive controls, the epic-tier test, the inprogress test, and `test_a_torn_working_log_shard_line_...`. No arena-combat tests are affected.
Adjacent: `tests/` for `event_seq_integrity_check` and `duplicate_run_record_check` (unchanged modules).

## New Tests Required
All integration-level, in `tests/tools/test_main_integrity_report.py`, using `_clean_repo`, `_w`, `_git`, `_report`:
1. `test_a_torn_runs_shard_line_is_reported_once_under_duplicate_runs` (AC1, AC3): runs shard with valid row, torn line, valid row; assert `findings["duplicate_runs"] == [f"{shard}:2: invalid JSON, skipped"]` (or contains it exactly once) and report completes; assert it is absent from `event_seq`.
2. `test_a_torn_events_shard_line_is_reported_once_under_event_seq` (AC2, AC3): events shard with seq 1, torn, seq 2; assert exactly one torn finding under `event_seq` and no spurious gap (valid rows on both sides still read); absent from `duplicate_runs`. Also a variant where valid rows around the tear contain a real duplicate seq, proving they still reach the check.
3. `test_non_dict_run_and_event_lines_are_skipped_silently` (AC4): lines `[1, 2]`, `"text"`, `3` in both runs and events shards; assert no finding and no exception (this fails today with AttributeError for events).
4. Optional: multiple shard files sorted order and per-file 1-based lineno with a preceding blank line.

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | integration | regression | `docs/agent-monitoring/README.md` "Main-branch integrity report"; sibling ticket TCK-20261008-...-TORN-WORKING-LOG-LINE; parity-ledger entry: none (oracle: none applicable) | one `<path>:<n>: invalid JSON, skipped` under duplicate_runs | `pytest tests/tools/test_main_integrity_report.py -k torn_runs` |
| 2 | integration | regression | same | same under event_seq | `-k torn_events` |
| 3 | integration | regression | same | duplicate/gap logic still sees rows before and after the tear | `-k torn` |
| 4 | integration | regression | same | non-dict lines yield no finding, no crash | `-k non_dict` |
| 5 | integration | regression | existing suite | all pass | full file command below |
Negative cases: non-dict lines, blank lines. Fixtures: existing `_clean_repo` helpers.

## Scoped Pytest Commands
`python3 -m pytest tests/tools/test_main_integrity_report.py -q`
Optionally `python3 -m pytest tests/tools -k "event_seq or duplicate_run" -q`. Never `pytest tests/`.

## Anti-Drift Test Guards
- Existing working_log torn-line test pins that `check_working_log` output is unchanged.
- Clean-ref test pins that no new findings appear on clean data.
- Dirty-tree test pins ref-only reading.
- CLI test pins exit 0 without `--strict`.
