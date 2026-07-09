---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260709-AGENT-MONITORING-DURATION
phase: open
date: 2026-07-09
tags: [agent-monitoring, data-quality]
---

# TCK-20260709-AGENT-MONITORING-DURATION

## Title
Compute duration_s at write time in record_run.py — schema marks it required but it's never populated

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`docs/agent-monitoring/schema.md` (line 43) documents `duration_s` as a **required** field on
every run record ("Wall-clock seconds from start to end. `null` for crashed runs."), with an
example value of `2910`. In practice, `tools/agent-monitoring/record_run.py`'s `REQUIRED` set is
`{"run_id", "start_ts", "workflow", "tier", "final_status"}` — `duration_s` is not required, not
computed, and not populated by any caller. Grepping every call site (`.claude/workflows/implement-ticket.js`,
`.claude/workflows/implement-epic.js`, `.claude/workflows/create-tickets.js`, and every manual
`record_run.py --data` invocation observed this session) confirms none of them pass `duration_s`
either — every record in `agent-monitoring/runs.jsonl` is missing it. This was discovered while
running `/agent-monitoring-retro` for 2026-W28: the generated report's "Avg duration" showed
"0 min" and "Slow Runs" was empty for a week that included standard-tier runs actually taking
10–35+ minutes end to end (verified directly from `start_ts`/`end_ts` on individual records), which
silently defeats the entire purpose of `tools/agent-monitoring/generate_retro.py`'s duration-based
sections (`avg_dur`, `slow_runs` at `generate_retro.py:181-182,240`) — they've never had real data
to report on since this field was speced.

## Scope
- In `tools/agent-monitoring/record_run.py`, compute `duration_s` at write time: parse `start_ts`
  and `end_ts` (both ISO 8601 `Z`-suffixed timestamps already present on every well-formed record —
  confirm this by checking actual caller payloads, not just the schema doc) and set
  `duration_s = (end_ts - start_ts).total_seconds()` as an integer, written into the record before
  it's appended to `agent-monitoring/runs.jsonl`. Do this unconditionally in the script itself —
  do not require every JS workflow call site to compute and pass it (that's the same "trust every
  caller to remember" failure mode `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` already
  fixed for the other REQUIRED fields).
- Per the schema's own documented exception, `duration_s` should be `null` for crashed runs (a
  record with no `end_ts` at all, if that's a real possibility for this script's callers — confirm
  whether `end_ts` is already enforced as REQUIRED before assuming this case exists).
- If a caller explicitly passes its own `duration_s` in `--data`, decide (and document the
  decision): does the computed value always win, or does an explicit caller-supplied value take
  precedence? Recommend: computed value always wins, since the whole point of this fix is to stop
  relying on caller-supplied correctness.
- Confirm `tools/agent-monitoring/generate_retro.py`'s existing duration-consuming code
  (`avg_dur`/`slow_runs`, lines ~181-182, ~240) needs no changes — it already reads `duration_s`
  correctly, it just never had real data.

## Out of Scope
- Backfilling `duration_s` on the ~552 historical run records that already exist in
  `agent-monitoring/runs.jsonl` without it (that's a one-off data migration, not this ticket's
  ongoing-correctness scope — flag as a possible follow-up if the retro process wants historical
  duration trends, but don't do it here).
- Any change to `record_events.py` or per-event `duration_ms` (that field is a separate,
  already-working mechanism per `docs/agent-monitoring/schema.md:217`, populated via
  `agent-monitoring/tools.jsonl`'s pre/post-hook timing — not affected by this gap).
- Re-running or backfilling past retro reports.

## Acceptance Criteria
- [ ] `record_run.py`'s written record always includes a non-null `duration_s` (integer seconds)
      whenever both `start_ts` and `end_ts` are present in the input, computed from those two
      fields regardless of whether the caller passed `duration_s` itself
- [ ] A record missing `end_ts` (if that's a real, valid input shape for this script) writes
      `duration_s: null`, matching the schema's documented crashed-run exception
- [ ] Running `/agent-monitoring-retro` (or `make agent-monitoring-retro`) after this fix, for a
      week containing at least one real run, shows a non-zero "Avg duration" whenever any run in
      that window actually took more than a few seconds — no longer flatlined at "0 min" by default
- [ ] Existing tests for `record_run.py` continue to pass, plus new tests covering: duration
      computed correctly from valid start/end timestamps, `duration_s: null` on missing `end_ts`,
      and (if adopted) computed value overriding a caller-supplied `duration_s`

## Related Tickets
- TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
- TCK-20260705-MONITORING-RUNID-JOIN

## Related Docs
- `docs/agent-monitoring/schema.md`
- `docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md`
- `agent-monitoring/retro/RETRO-2026-W28.md` (Notes section — where this gap was first documented)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/agent-monitoring/record_run.py`
- `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_record_run.py` (if it exists — check during investigation)

## Assumptions / Open Questions
- Assumes `end_ts` is reliably present on every well-formed run record by the time `record_run.py`
  is called (all observed call sites in `.claude/workflows/*.js` compute `END_TS` via `date -u` and
  substitute it before calling this script) — if a genuinely crash-only path exists where `end_ts`
  is legitimately absent, `duration_s: null` should follow naturally rather than erroring.
- Open question for planning: should this also add `duration_s` to `record_run.py`'s `REQUIRED`
  set (making its *absence from output* a hard write-time failure, mirroring how
  `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` treated the other required fields), or is
  computing it unconditionally in the script sufficient on its own since a script-internal
  computation can't be "forgotten" the way a caller-supplied field can?

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary
