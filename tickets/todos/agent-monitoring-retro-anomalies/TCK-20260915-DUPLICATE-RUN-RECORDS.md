---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-DUPLICATE-RUN-RECORDS
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-DUPLICATE-RUN-RECORDS

## Title
60 runs are written twice with identical `run_id`, `execution_id` and `start_ts` — every run-count metric, including the retro's own headline, is inflated by an unknown amount

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Sweeping `agent-monitoring/data/*/runs.jsonl` (1,609 records) found **142 `run_id`s with more than
one run record**. Splitting them by whether the duplicates are distinguishable:

- **82 carry a distinct `execution_id` or `start_ts`** — legitimate re-runs of the same ticket. Not
  a defect.
- **60 carry an identical `execution_id` AND an identical `start_ts`** — the same run recorded
  twice, with nothing to tell the copies apart.

Sample of the ambiguous-looking group (distinct starts, so *not* in the 60): `TCK-20260606-DOCSITE-
SCHEMA` has two DONE records at `01:06:18` and `01:13:36`; `TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH`
at `13:36:07` and `13:44:38`. Those are re-runs. The 60 are the ones where even that distinction
is absent.

**Consequence, and the reason this is first in the epic:** every count derived from `runs.jsonl`
is inflated. The 2026-09-15 two-week review reports 249 runs and a 93% DONE rate; neither figure
can be trusted until the size of the duplication inside the window is known. Nothing currently
flags this — `agent-monitoring-validate` checks that records *exist*, not that they are unique.

## Scope
- Determine whether this is a write-path defect (something appends a run record twice) or an
  expected consequence of some workflow re-entry pattern that reuses `run_id` and `execution_id`.
  Start from `tools/agent-monitoring/record_run.py` and the `writeMonitoring` path in
  `.claude/workflows/implement-ticket.js`.
- Measure how many of the 60 fall inside recent windows (7/14/28 days) versus historical, so the
  retro can state a corrected figure or an explicit uncertainty.
- Decide the disposition: dedupe on read, prevent on write, or accept-and-document. All three are
  legitimate; silently leaving it is not.

## Out of Scope
- Rewriting or deleting historical `runs.jsonl` rows. If dedupe-on-read is chosen, the corpus stays
  as-is.
- The 82 legitimate re-runs.
- `seq` duplication inside events — that is `TCK-20260915-EVENT-SEQ-INTEGRITY`.

## Acceptance Criteria
- [ ] The cause is identified, or explicitly recorded as not-determinable with the evidence
      available.
- [ ] The count inside the last 14 days is measured, so the retro's run count can be corrected or
      caveated.
- [ ] A disposition is recorded (prevent / dedupe-on-read / accept), with its reason.
- [ ] If a detector is added, it **ratchets from the measured baseline (60)** and does not assert
      zero — see `SEQUENCE.md`'s ratchet discipline note.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-MONITORING-ANOMALY-VALIDATOR` — the capstone detector, scoped after this

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/record_run.py`
- `.claude/workflows/implement-ticket.js` (the `writeMonitoring` path)
- `agent-monitoring/data/*/runs.jsonl`

## Assumptions / Open Questions
- Whether `execution_id` is *supposed* to be unique per run record is itself unconfirmed — check
  `docs/agent-monitoring/schema.md` before treating identical values as proof of duplication.
- The 60/82 split was computed on the whole corpus, not the recent window. Re-derive.

## Implementation Notes
Reproduce with a direct scan of the shards rather than `monitoring.db` (stale since 2026-09-13).

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
