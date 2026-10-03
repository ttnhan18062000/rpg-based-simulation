---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260915-DUPLICATE-RUN-RECORDS
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Plan — TCK-20260915-DUPLICATE-RUN-RECORDS

## `tools/agent-monitoring/run_dedup.py` (new — already written during investigation)

`execution_key`, `group_runs_by_execution`, `latest_in_group`, `dedupe_to_latest_per_execution`,
`classify_duplicate_groups`. See its own module docstring for the grouping rules and the
false-positive it was corrected for before shipping (two unrelated legacy records both missing
`start_ts`).

## `tools/agent-monitoring/generate_retro.py`

Wire `dedupe_to_latest_per_execution` into `main()`'s three branches (`--all`, `--days`, week
default), applied to the window-filtered `runs` list *before* re-deriving `run_ids`/`events`/
`tools` from it — so every downstream consumer (`compute_retro_metrics`, tier/tag breakdowns,
outlier detection) sees one row per real execution automatically, not just the top-level
`run_summary.total`/`done_count`. Import `run_dedup` at module level alongside the existing
`agent-monitoring` tool imports.

Add one new section to the rendered report (`generate()`'s Markdown output) noting the raw vs.
deduplicated run count when they differ, so a reader sees the correction inline rather than having
to know this ticket exists.

## Ratchet check

New `tools/gate_checks/duplicate_run_record_check.py`, same shape as this batch's own established
convention (`working_log_duplicate_check.py`/`working_log_content_duplicate_check.py`): a
`check_duplicate_run_records()` function returning `[{"status": "PASS"|"FAIL", "evidence": ...}]`,
`MARKER:` + `json.dumps()` in `__main__`. Ceiling: **1** (the measured `identical_outcome` baseline)
— ratchets, never asserts zero, per `SEQUENCE.md`'s own discipline note and this session's
established precedent (`TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT`,
`TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` items 1/6).

Not wired into a blocking gate in this ticket — no existing call site in `implement-ticket.js` or a
Makefile target currently checks anything about `runs.jsonl` duplication, and the epic's own capstone
(`MONITORING-ANOMALY-VALIDATOR`, ticket 8) is where the actual wiring decision belongs, once it can
see all seven other tickets' own confirmed causes together rather than wiring each one ad hoc. This
ticket ships the check function + its own tests + Makefile target for manual/CI-optional use,
matching how item 1 of `MONITORING-SURFACE-DEAD-MECHANISMS` shipped its own check before that
ticket's capstone (this epic doesn't have a direct capstone predecessor to point to, but the shape
is the same: build the verified mechanism now, let ticket 8 decide final wiring).

## `RETRO-LAST14D.md` — the epic's own AC #3 ("written back into the retro's notes, not left in
## ticket bodies")

Append a small, targeted note (not a regeneration — the file has hand-authored sections that a
`generate_retro.py --days 14` CLI run would destroy, confirmed the hard way during investigation)
recording: the corrected 247/232/93.9% figures, the 66/63/2/1 classification, and a pointer to this
ticket for detail. Use `Edit`, never the CLI, on this file going forward.

## Tests

- `tests/tools/test_run_dedup.py` (new): `execution_key` grouping rules including the
  missing-start_ts false-positive fix (a real regression fixture proving two None-start_ts records
  are NOT merged); `dedupe_to_latest_per_execution` picks the highest-`end_ts` record; a real-corpus
  test pinning the measured 66/63/2/1 classification (ratchet-shaped: exact-match on the smaller,
  stable numbers is fine here since they're a closed historical count, not a growing live one —
  unlike `working_log.csv`, `runs.jsonl`'s all-time history for dates before this ticket is fixed).
- `tests/tools/test_generate_retro.py`: extend with a fixture proving `--days`/`--all`/week
  generation now dedupes before computing `run_summary`.
- `tests/tools/test_duplicate_run_record_check.py` (new): ratchet pass/fail, ceiling-may-only-
  decrease pin, real-corpus check, Makefile wiring — mirrors `working_log_duplicate_check.py`'s own
  test shape exactly.
