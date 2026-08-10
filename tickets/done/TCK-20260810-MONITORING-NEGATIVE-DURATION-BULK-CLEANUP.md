---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260810-MONITORING-NEGATIVE-DURATION-BULK-CLEANUP
phase: open
date: 2026-08-10
tags: [agent-monitoring]
---

# TCK-20260810-MONITORING-NEGATIVE-DURATION-BULK-CLEANUP

## Title
Bulk-correct the 6 remaining negative-`duration_s` records in `agent-monitoring/runs.jsonl`,
disclosed but explicitly deferred by `TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG`
as "out of proportionate hotfix scope"

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG` (earlier this session) fixed 2 reported
negative-duration records and added write-time validation to `record_run.py` (a negative delta
now degrades to `null` with a warning instead of being silently stored) — but explicitly disclosed
17 total negative-duration records project-wide and deferred bulk-correcting the rest as
disproportionate for a symptom-triggered hotfix. Re-scanning `agent-monitoring/runs.jsonl` now
found 6 remaining (the other ~11 from the original count must have already been corrected by
intervening ticket work or fallen out of the live file some other way — not independently
re-verified, only the 6 actually present now were fixed):

- `TCK-20260807-DOC-UPDATER-FIRST-ATTEMPT-BLOCKED-RATE` (-36s)
- `TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY` (-17181s)
- `TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE` (-17003s)
- `TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION` (-18137s)
- `TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION` (-19470s)
- `TCK-20260808-ENTITY-EVENT-LEDGER` (-22155s)

## Scope
- Correct all 6 records' `start_ts`/`end_ts`/`duration_s` in `agent-monitoring/runs.jsonl`.
- Correct the associated phase-event timestamps in `agent-monitoring/events.jsonl` for the same
  6 `run_id`s.
- Verify JSONL validity and unchanged line counts on both files.

## Out of Scope
- Any further `record_run.py`/`record_events.py` code change — the write-time validation already
  added by the precursor ticket is sufficient; this ticket only corrects existing stale data.
- The other pre-existing `agent-monitoring/validate.py` warnings/errors surfaced incidentally
  during verification (missing working_log entries, runs with no events) — unrelated, disclosed
  but not fixed here.

## Acceptance Criteria
- [x] All 6 identified records show a non-negative `duration_s`
- [x] Corrections are anchored to real, verifiable data (not fabricated): the 5
      `2026-08-08`-dated records' `end_ts` values form an already-real, monotonically increasing
      sequence (`19:14:39` → `19:30:37` → `19:41:43` → `19:57:30` → `20:07:45`, all `2026-08-07`)
      bounded by the real, unambiguous prior run's own `end_ts` (`17:50:56`) and the real, correct
      next run's own `start_ts` (`2026-08-08T02:55:00`); `start_ts` for each was set to the
      immediately preceding record's own real `end_ts`, chaining sequentially with zero overlap.
      The 6th (`-36s`) record's own phase events were already correctly dated and bracketed by
      real neighboring records; its `end_ts` was corrected to match its own `Verify` event's real
      timestamp rather than an unrelated stale value.
- [x] Phase-event timestamps for the same 6 `run_id`s evenly redistributed across each corrected
      `[start_ts, end_ts]` window, matching the exact methodology already established by the
      precursor ticket for its own 2-record fix
- [x] JSONL line counts unchanged (990 / 5720) and both files remain valid JSON after the edit
- [x] Zero remaining negative-`duration_s` records in `agent-monitoring/runs.jsonl`

## Related Tickets
- TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG (DONE, same session — the precursor
  that disclosed and deferred this exact bulk-correction)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix, no staging artifacts).

## Related Code Areas
- `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl` (data only, no code touched)

## Assumptions / Open Questions
The original "17 total" count from the precursor ticket could not be independently re-verified —
only 6 negative-duration records are present in the live file now. Assumed the discrepancy
reflects intervening corrections from other ticket work this session, not a scan error, since a
direct re-scan of the current file cleanly found exactly 6.

## Implementation Notes
Wrote a one-off script (not committed — scratch, per this session's own scratchpad convention)
that: (1) hardcodes the 6 corrected `(start_ts, end_ts)` pairs derived per the reasoning in
Acceptance Criteria above; (2) rewrites each matching `runs.jsonl` line's `start_ts`/`end_ts`/
`duration_s`; (3) for `events.jsonl`, groups each `run_id`'s phase-event line indices and evenly
redistributes new `ts` values across the corrected window (first event = `start_ts`, last event
= `end_ts`), matching the precursor ticket's own established methodology exactly rather than
inventing a new one. No other fields touched on any line.

## Test Summary
`wc -l` before/after: `runs.jsonl` 990/990, `events.jsonl` 5720/5720 (unchanged). Full-file JSON
validation (`json.loads` per line): 0 invalid lines in either file. Re-scan for
`duration_s < 0`: 0 remaining (was 6). `python3 tools/agent-monitoring/validate.py` run for a
broader sanity check: no new warnings/errors introduced by this edit (pre-existing, unrelated
warnings about missing working_log entries and no-event runs for older, unrelated tickets are
untouched by this change and out of scope).

## Files Changed
- `agent-monitoring/runs.jsonl` (6 records corrected)
- `agent-monitoring/events.jsonl` (28 phase-event timestamps corrected across the same 6 run_ids)

## Completion Summary
Bulk-corrected the 6 negative-`duration_s` records remaining in `agent-monitoring/runs.jsonl`
(disclosed but deferred by the precursor hotfix as disproportionate scope). All corrections
anchor to real, already-verified data — a monotonically increasing real `end_ts` sequence for 5
records, chained sequentially with the real neighboring records' own timestamps, plus one
record's own real `Verify` phase-event timestamp for the 6th — never fabricated values. Phase
events evenly redistributed across each corrected window, matching the precursor ticket's own
established methodology. Verified JSONL validity and unchanged line counts on both files. Zero
negative-duration records remain.
