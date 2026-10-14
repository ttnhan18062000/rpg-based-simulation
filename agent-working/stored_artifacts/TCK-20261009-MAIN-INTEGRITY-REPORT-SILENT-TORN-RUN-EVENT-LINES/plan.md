---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES
artifact_type: plan
tags: [agent-monitoring, data-quality]
---

# Implementation Plan — TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES

## Summary
Change `_load_rows` in `tools/agent-monitoring/main_integrity_report.py` to return `(rows, torn)`, where `torn` holds `"<path>:<lineno>: invalid JSON, skipped"` strings (mirroring `check_working_log`, lines 108-120) and non-dict parsed values are dropped silently. `check_duplicate_runs` and `check_event_seq` prepend the torn strings to their findings. Tests are added first (red), then the code change, then docs. Report-only behavior is unchanged.

## Steps

### Step 1 - Add failing tests
**Files:** tests/tools/test_main_integrity_report.py
**Change:** Using existing helpers `_clean_repo`, `_w`, `_git`, `_report` (read the file first and copy the call style of `test_a_torn_working_log_shard_line_is_reported_and_the_rows_around_it_still_count`, ~lines 210-222), add:
1. `test_a_torn_runs_shard_line_is_reported_once_under_duplicate_runs` (AC1, AC3): runs shard with valid row, torn line (line 2), valid row. Assert `findings["duplicate_runs"]` contains `f"{shard}:2: invalid JSON, skipped"` exactly once, the torn string is absent from `event_seq`, and the report completes.
2. `test_a_torn_events_shard_line_is_reported_once_under_event_seq` (AC2, AC3): events seq 1, torn, seq 2. Assert exactly one torn finding under `event_seq`, no gap finding, absent from `duplicate_runs`. Add a variant where rows around the tear contain a real duplicate seq to prove they still reach the check.
3. `test_non_dict_run_and_event_lines_are_skipped_silently` (AC4): lines `[1, 2]`, `"text"`, `3` in both a runs and an events shard; no findings, no exception.
4. Optional: two shards, sorted order, per-file 1-based lineno with a preceding blank line counted.
**Do NOT touch:** existing tests; `check_working_log` test.
**Verify:** `python3 -m pytest tests/tools/test_main_integrity_report.py -q -k "torn or non_dict"` - new tests fail before Step 2 (test 3 fails with AttributeError for events, per `event_seq_integrity_check.py:54-56` `e.get`).

### Step 2 - `_load_rows` returns torn lines and filters non-dicts
**Files:** tools/agent-monitoring/main_integrity_report.py (`_load_rows`, currently lines 173-183)
**Change:** Signature `_load_rows(reader, kind) -> tuple[list[dict], list[str]]`. Keep the sorted-path iteration and regex. Use `for lineno, line in enumerate(reader.show(p).splitlines(), 1)`; skip blank lines (still counted in lineno); on `ValueError` append `f"{p}:{lineno}: invalid JSON, skipped"` to `torn` and continue; append to `rows` only if `isinstance(row, dict)`. Only caller pair is the two checks below (investigation: grep shows no other callers).
**Do NOT touch:** `check_working_log` (lines 108-120), `_SHARD_RE`, RefReader.
**Verify:** compiles; completed together with Step 3 for tests.

### Step 3 - Fold torn strings into the two checks
**Files:** tools/agent-monitoring/main_integrity_report.py (`check_duplicate_runs`, `check_event_seq`, ~lines 186-196)
**Change:** `rows, torn = _load_rows(reader, "runs")`; return `torn + [evidence ... non-PASS]`. In `check_event_seq`, `rows, torn = _load_rows(reader, "events")`; return `torn + dup findings + gap findings`. Torn lines come first, in sorted path/line order (deterministic). Each `_load_rows` call happens once per kind, so each torn line is reported once, runs only under duplicate_runs, events only under event_seq. `build_report` and `render` shape (`findings: dict[str, list[str]]`) is unchanged.
**Do NOT touch:** `duplicate_run_record_check.py`, `event_seq_integrity_check.py`, `run_dedup.py`, `build_report`, `render`, exit-code/`--strict` logic.
**Verify:** `python3 -m pytest tests/tools/test_main_integrity_report.py -q` (all new and existing pass: AC1-AC5); optionally `python3 -m pytest tests/tools -k "event_seq or duplicate_run" -q`.

### Step 4 - Update docs and module docstring
**Files:** tools/agent-monitoring/main_integrity_report.py (module docstring check list, lines ~21-24); docs/agent-monitoring/README.md ("Main-branch integrity report" paragraph, ~line 280-289)
**Change:** In the `duplicate_runs` and `event_seq` docstring entries and in the README sentence ending "duplicate-run records and event-seq duplicates/gaps", add that a torn (unparseable) line in a runs/events shard is named as `<path>:<lineno>: invalid JSON, skipped` under the matching check instead of being dropped, and non-dict lines are ignored. Docs-only wording.
**Do NOT touch:** any other README section, parity ledger, mechanics docs.
**Verify:** re-run full test file; `make knowledge-index-update` after docs edit (per CLAUDE.md).

## Scope Guards
- Do not touch `check_working_log`, `duplicate_run_record_check`, `event_seq_integrity_check`, `run_dedup`, or any gate wiring.
- Do not repair/filter real torn lines on main; do not make the report exit non-zero by default; keep ref-only reading (never working tree).
- Keep sorted path order and 1-based line numbers counting blank lines.
- Do not change the report JSON/`render` shape.
- No parity-ledger or mechanics changes (none overlap).

## Dependency Map
Step 1 independent. Steps 2 and 3 are one atomic change (the signature change breaks the callers until both are done); run tests after Step 3. Step 4 after Step 3.

## Acceptance Criteria Map
| AC | Steps | Test |
|---|---|---|
| 1 torn runs line, one finding, duplicate-runs | 1, 2, 3 | test_a_torn_runs_shard_line_is_reported_once_under_duplicate_runs |
| 2 torn events line, event-seq | 1, 2, 3 | test_a_torn_events_shard_line_is_reported_once_under_event_seq |
| 3 valid rows around tear still checked | 2, 3 | duplicate-seq variant in the events test; valid rows in runs test |
| 4 non-dict skipped, no finding/crash | 2 | test_non_dict_run_and_event_lines_are_skipped_silently |
| 5 existing tests pass | 3 | full `tests/tools/test_main_integrity_report.py` |

AC cross-check: the AC wording (path + 1-based line number, per-check placement, non-dict skipped) matches Steps 2-3 exactly; the string format matches the ticket Scope.

## Anti-Drift Notes
- Non-dict filtering is required, not optional: today `e.get` raises AttributeError on events, and `run_dedup.classify_duplicate_groups` also calls `.get` on rows (`run_dedup.py:107-108`).
- Real torn lines on main will become new report-only findings once this lands; intended.
- Shared resource: `_load_rows` has only these two readers; the `findings` dict is written only by `build_report`; no concurrent writers.

## Unresolved Questions
None.
