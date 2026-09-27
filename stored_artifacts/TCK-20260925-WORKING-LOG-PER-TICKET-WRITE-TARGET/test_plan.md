---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET
artifact_type: test_plan
tags: [workflows, agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET

1. **AC1** — `test_working_log_writer.py::test_two_working_log_shards_never_conflict_under_
   sequential_squash_merges`: real throwaway git repo, two branches each adding their own
   `.working_log.jsonl` shard, sequential squash-merges, asserts a clean `git merge` with both
   files present.
2. **AC2** — `test_done_checker_static.py::test_working_log_no_row_yet_fails_when_row_only_
   pending_in_shard` / `test_working_log_exactly_one_row_passes_via_pending_shard_only`: empty CSV,
   a row only in a pending shard, both checks see it correctly without any consolidation call.
3. **AC3** — `test_working_log_exactly_one_row_reopen_across_csv_and_pending_shard_passes` (a
   BLOCKED row already consolidated + a DONE row still pending → PASS, reopen) and `..._
   duplicate_across_csv_and_pending_shard_fails` (two DONE rows split the same way → FAIL).
4. **AC4** — `test_consolidate_pending_rows_orders_by_timestamp_across_multiple_shards`: two
   shards named so alphabetical order would scramble true chronological order; asserts the
   consolidated CSV's row order follows `timestamp`, not the glob.
5. **AC5** — `test_consolidate_pending_rows_is_idempotent`: running consolidation twice produces
   no duplicate row and reports `{"consolidated_rows": 0, "shard_files": 0}` on the second run.
6. **AC6** — existing `TestDuplicateWorkingLogRowRefused` tests (updated to consolidate before
   asserting where they check the CSV) confirm `record_hand_orchestrated_closure.py` and
   `append_working_log_row()` still agree: a direct call followed by the closure tool for the same
   `(ticket_id, title)` still refuses with a non-zero exit.
7. **AC7** — full `tests/tools/` regression scoped run (this touches widely-imported modules).

Also: `test_append_working_log_row_stages_without_touching_canonical_csv` (no `path` given never
touches the CSV) and `test_consolidate_pending_rows_merges_with_pre_existing_canonical_content` /
`..._no_shards_is_a_no_op` / `..._missing_data_root_is_a_no_op`, mirroring
`test_monitoring_consolidation.py`'s own equivalent edge-case coverage for the JSONL shards.
