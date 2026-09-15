---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-MONITORING-INTEGRITY-BACKLOG
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-MONITORING-INTEGRITY-BACKLOG

## Title
`make agent-monitoring-validate` is red today, 34 September closures have no run record, and 9 working_log rows break the CSV schema — a backlog of integrity debt that no report surfaces

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Five related integrity defects, grouped because each is small and they share one question: which of
these do we fix, and which do we accept and document?

**1. The integrity gate is failing right now.** `make agent-monitoring-validate` exits non-zero with
19 warnings of the form "Run marked DONE has no working_log entry". All 19 are June-era
(`TCK-20260619-*`, `TCK-20260629-SIMQ-*`). A permanently-red gate trains people to ignore it — the
same failure mode `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` describes.

**2. 34 September closures have no run record at all**, clustered on 2026-09-02 (4), 09-03 (13),
09-04 (14), 09-05 (3). The tight clustering points at one hand-orchestrated batch rather than steady
leakage — the gap `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` addressed.

**3. 9 of 2,013 `working_log.csv` rows (0.4%) do not match the 6-column schema** — 4 rows with 7
fields, 2 with 8, 3 with 9. Cause is unescaped commas in the **title** field, e.g.
`"Clan lifecycle -- joining, leaving, and succession-on-death (M4 idea 40)"`, which shifts every
later column so the status column contains prose. Any status-based query silently misreads them;
this review hit exactly that while counting closures by status.

**4. 66 runs and 55 events carry an unusable `ts`** (None, or a float/int epoch where consumers
expect an ISO string). All 66 runs are W24–W27 (June), so recent windows are not deflated — but any
time-windowed query silently drops them.

**5. `agent-monitoring/data/unknown-week/` holds 34 rows** — the shard rows land in when no week
key can be derived (29 of them have `ts: None`).

## Scope
- For each of the five: fix, or accept with a written reason. A per-item disposition is the
  deliverable; a blanket "cleanup" is not.
- Item 1 specifically needs a decision on the gate: backfill the 19, exclude pre-schema records, or
  ratchet — but it should not stay red indefinitely.
- Item 3 needs the **writer** fixed (title-field quoting) as well as any decision about the 9
  existing rows.

## Out of Scope
- Rewriting `working_log.csv` history beyond the 9 malformed rows, if repair is chosen at all.
- The duplicate-row ratchets from `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` (84 duplicate
  `ticket_id`s, 46 `(ticket_id, title)` pairs) — those deliberately freeze a historical baseline and
  are not this ticket's to touch.

## Acceptance Criteria
- [ ] `make agent-monitoring-validate` either passes, or fails only on a ratcheted baseline with the
      reason recorded.
- [ ] Each of the five items has a recorded disposition.
- [ ] The working_log writer quotes fields containing commas, with a test proving a comma-bearing
      title round-trips.
- [ ] Any detector ratchets from measured baselines; none asserts zero.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (done)
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` (done) — established the sole sanctioned writer
- `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` (done)

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260912-WORKING-LOG-APPEND-HELPER/`

## Related Code Areas
- `tools/agent-monitoring/validate.py`
- `tools/working_log_writer.py` (`append_working_log_row`)
- `tools/agent-monitoring/record_run.py`, `record_events.py`
- `agent-monitoring/data/unknown-week/`

## Assumptions / Open Questions
- Items 1, 4 and 5 are all historical (June-era). Accepting them with an explicit exclusion may be
  more honest than backfilling records nobody can reconstruct.
- Item 2's clustering strongly suggests one batch; identifying which session closed those 34 would
  confirm it, and is worth doing before deciding.

## Implementation Notes
Derive from the shards directly. Note that `agent-monitoring-validate` currently exits 1, so any
script chaining off it needs to handle that.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
