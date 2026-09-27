---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS
artifact_type: test_plan
tags: [workflows, process-improvement, agent-monitoring]
---

# Test Plan — TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS

In `tests/tools/test_done_checker_static.py`, `check_data_runs_clean` section:

1. Rename `test_data_runs_clean_unparsable_start_ts_flags_any_file` →
   `test_data_runs_clean_absent_start_ts_no_ticket_context_is_indeterminate`; assert
   `status == "INDETERMINATE"` (was `"FAIL"`), and that the evidence mentions `--start-ts`.
2. New: `test_data_runs_clean_present_garbage_start_ts_still_flags_any_file` — an actual malformed
   non-None string (e.g. `"not-a-date"`), asserting `FAIL` (AC4's fail-closed rule for a genuinely
   unparsable explicit value, distinct from an absent one).
3. New: `test_data_runs_clean_resolves_start_ts_from_own_run_record_pass` — scratch
   `agent-monitoring/data/2026-W23/runs.jsonl` with `{"run_id": ticket_id, "start_ts": "<iso>"}`,
   `ticket_id` given, no explicit `start_ts`, all files older than the recorded one — `PASS`,
   evidence names the run-record source.
4. New: `test_data_runs_clean_resolves_start_ts_from_own_run_record_fail` — same fixture shape, one
   file newer than the recorded `start_ts` — `FAIL`, evidence still names the file.
5. New: `test_data_runs_clean_ticket_id_with_no_matching_run_record_is_indeterminate` — `ticket_id`
   given, `runs.jsonl` exists but has no row for it — `INDETERMINATE`, not `FAIL`.
6. Existing 5 real-`start_ts` tests — unchanged, expected to still pass byte-identically.
7. All `clean_data_runs_early`/shared-walk tests — unchanged, `clean_data_runs_early` itself is not
   modified (Out of Scope).

Run scope: `tests/tools/test_done_checker_static.py -v`, then a broader
`tests/tools/ -m "not slow and not extra_slow"` regression pass (AC6).
