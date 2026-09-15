---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260915-DUPLICATE-RUN-RECORDS
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20260915-DUPLICATE-RUN-RECORDS

| AC | Test |
|---|---|
| Cause identified | `test_run_dedup.py`'s real-corpus classification test pins 66/63/2/1, backed by investigation.md's direct event-log correlation (not itself a unit test — narrative evidence) |
| 14-day count measured | `test_generate_retro.py` extension proves `--days 14` now returns the deduplicated `run_summary`; investigation.md records the raw-vs-deduped numbers |
| Disposition recorded | plan.md + this ticket's own Completion Summary |
| Ratchet if a detector is added | `test_duplicate_run_record_check.py`'s ceiling-may-only-decrease pin |

## Regression coverage

- `tests/tools/test_run_dedup.py` (new) — grouping correctness, the missing-start_ts false-positive
  fix, latest-record selection, real-corpus classification pin.
- `tests/tools/test_generate_retro.py` — extend, don't replace; confirm existing tests still pass
  (dedup must not change any already-tested single-execution-per-run_id fixture's result).
- `tests/tools/test_duplicate_run_record_check.py` (new) — same shape as
  `test_working_log_duplicate_check.py`.
- Full `tests/tools/test_generate_retro.py` + new files run together before commit.

## Manual verification

- Confirm `agent-monitoring/retro/RETRO-LAST14D.md`'s hand-authored sections survive the note
  edit (diff review, not a CLI regen).
- `make duplicate-run-record-check` (once wired) runs and reports PASS against the real corpus.
