---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET
artifact_type: plan
tags: [workflows, agent-monitoring, process-improvement]
---

# Plan — TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET

## 1. `tools/working_log_writer.py`

- `_append_csv_row(fields, path=_WORKING_LOG_PATH)` — the old `append_working_log_row()` body,
  extracted verbatim (the one place that opens the CSV in write mode).
- `append_working_log_row(...)`: if `path` is given, calls `_append_csv_row` directly (unchanged
  test-facing behavior). If omitted (every real caller), writes one JSON line to
  `monitoring_batch_identifier.resolve_write_target("working_log")`.
- `consolidate_pending_rows(data_root=agent-monitoring/data, csv_path=tickets/working_log.csv)` —
  globs `*/*.working_log.jsonl`, collects every row, sorts by `timestamp`, appends each via
  `_append_csv_row`, deletes the consumed shard files. Returns `{"consolidated_rows", "shard_files"}`.

## 2. `tools/working_log_parser.py`

- `parse_pending_working_log_shards(data_root=agent-monitoring/data)` — read-only, returns every
  pending shard row as a dict (already shaped with the 6 `HEADER_FIELDS` keys).

## 3. `tools/agent-monitoring/record_hand_orchestrated_closure.py`

- `_existing_row_for()` gains a `data_root` parameter and also checks
  `parse_pending_working_log_shards()`'s rows after the CSV scan, preserving the double-write
  refusal across the staged/consolidated split.

## 4. `tools/gate_checks/done_checker_static.py`

- `_count_rows_for_ticket`/`_rows_for_ticket` gain a `data_root` parameter, combining the CSV scan
  with `_pending_rows_for_ticket_as_lists()` (a new small helper converting pending dicts to the
  same raw-list shape via `HEADER_FIELDS`) before applying the existing matching logic unchanged.
- `check_working_log_no_row_yet`/`check_working_log_exactly_one_row` thread `data_root` through.

## 5. `tools/agent-monitoring/monitoring_consolidation.py`

- Imports and calls `working_log_writer.consolidate_pending_rows()` once from `consolidate_all()`
  (not per-week, since the canonical file isn't week-sharded); reports its result under a
  `"working_log"` key. `main()`'s human-readable printer special-cases that key's different shape.
- Module docstring's "Scope note: NOT consolidated here" corrected to reflect landing.

## 6. Tests

- `test_working_log_writer.py`: new staging/consolidation section (ordering-by-timestamp across
  multiple shards — AC4; idempotency — AC5; merge-with-existing-content; no-op cases) plus a real-
  git-repo squash-merge fixture mirroring the shard ticket's own `test_monitoring_consolidation.py`
  pattern exactly, for `.working_log.jsonl` (AC1).
- `test_done_checker_static.py`: new section proving both checks see a pending-only row (AC2) and
  that the reopen-vs-duplicate distinction holds when the two rows are split across the CSV and a
  pending shard, in both directions — legitimate reopen (PASS) and real duplicate (FAIL) (AC3).
- `test_record_hand_orchestrated_closure.py`: the existing `TestWorkingLogCsvAppended`/
  `TestDuplicateWorkingLogRowRefused` tests that assert on the CSV directly after running the
  script now consolidate first (a one-line addition per test, via a shared `_consolidate()`
  helper) — their original assertions are otherwise unchanged, since consolidation is a read-
  transparent step for what they were already checking. One test
  (`..._parent_dir_warns_but_does_not_fail...`) is retitled/re-asserted: the scenario it captured
  (an `OSError` from a missing `tickets/` dir) can no longer occur at all now that the write
  target self-creates its own parent dirs under `agent-monitoring/data/` — a strictly stronger
  guarantee, not a regression, and the test now proves that directly rather than asserting a
  warning that no longer fires.

## 7. Verification

Every directly touched test file, then the full `tests/tools/` regression (this touches widely-
imported modules: `working_log_writer.py`/`working_log_parser.py` are imported by both the
pipeline's Finalize step and the hand-orchestrated closure tool).
