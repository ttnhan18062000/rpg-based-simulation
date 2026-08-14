---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260709-AGENT-MONITORING-DURATION
phase: done
date: 2026-07-09
tags: [agent-monitoring, data-quality]
---

# TCK-20260709-AGENT-MONITORING-DURATION

## Title
Compute duration_s at write time in record_run.py — schema marks it required but it's never populated

## Status
DONE

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
- Added `compute_duration_s(record)` to `tools/agent-monitoring/record_run.py`: returns
  `int((end - start).total_seconds())` parsed via `datetime.fromisoformat(ts.replace("Z", "+00:00"))`
  (same pattern already used in `post_tool_hook.py` / `generate_retro.py` for this repo's `Z`-suffixed
  timestamps), or `None` if `end_ts` is absent/null. Called unconditionally in `main()` after
  `validate_record()` passes and before the record is appended, so `record["duration_s"]` is always
  set (possibly to `None`) regardless of whether the caller included it in `--data`.
- Confirmed via `.claude/workflows/*.js` (`implement-ticket.js:234`, `implement-epic.js:250`,
  `create-tickets.js:135`, `simq-audit.js:78`) that every real call site invokes `record_run.py`
  exactly once, at the very end of the run, with `end_ts` already substituted from a `date -u` capture
  — there is no separate "write IN_PROGRESS record at start" call anywhere. A true crash (process killed
  mid-run) means this final call never fires at all, so no run record is written for that run_id —
  `docs/agent-monitoring/schema.md`'s CRASHED status is synthesized by `validate.py` from records that
  exist with `start_ts` but no `end_ts`, which is a shape `record_run.py` must tolerate even though no
  current caller produces it directly. `end_ts` is intentionally left out of `REQUIRED` (unchanged) so
  this shape stays legal to write; `compute_duration_s` returns `None` for it rather than erroring.
- Design decision (resolving the ticket's "always wins?" question): the computed value always
  overwrites any caller-supplied `duration_s` in `--data` — `record["duration_s"] = compute_duration_s(record)`
  runs unconditionally after validation, with no branch that checks for a pre-existing value. This is
  the ticket's own recommendation and matches the stated goal of not depending on caller correctness.
- Resolved the ticket's open question (add `duration_s` to `REQUIRED`?): **no**. `REQUIRED` enforces
  that a *caller* didn't forget to supply something; `duration_s` is no longer caller-supplied at all —
  it's computed by the script itself immediately before every write, so there's no "forgot to pass it"
  failure mode left to guard against. Adding it to `REQUIRED` would only reject records that are
  missing `end_ts` (the legitimate crashed-run shape per schema.md), which is exactly the case this
  field is supposed to represent as `null`, not reject. Enforcing it in `REQUIRED` would be enforcing
  the wrong thing.
- Confirmed `generate_retro.py` needs no changes: `durations = [r["duration_s"] for r in runs if r.get("duration_s")]`
  (line 181) and `slow_runs = [r for r in runs if (r.get("duration_s") or 0) > 1800]` (line 240) already
  read `duration_s` via truthy/`.get()` checks that treat missing, `None`, and `0` all as "no data" —
  correct behavior for both the historical gap (field absent) and the new crashed-run case
  (field explicitly `None`). No change made to this file.

## Test Summary
Added to `tests/tools/test_record_run.py` (pre-existing file, extended rather than created):
`test_compute_duration_s_from_valid_start_and_end`, `test_compute_duration_s_none_when_end_ts_missing`,
`test_compute_duration_s_none_when_end_ts_null` (pure-function tests against `compute_duration_s`), and
`TestDurationWrittenToRecord` (3 subprocess-level tests run against `tmp_path` cwd, never touching the
real `agent-monitoring/runs.jsonl`): duration computed and written correctly, `duration_s: null` written
when `end_ts` is absent, and a caller-supplied `duration_s: 99999` in `--data` is overwritten by the
computed value. Ran `pytest tests/tools/test_record_run.py tests/tools/test_record_events.py
tests/tools/test_generate_retro.py` — all 44 tests pass (13 + 31), confirming no regression in sibling
monitoring-tool tests.

## Files Changed
- `tools/agent-monitoring/record_run.py`
- `tests/tools/test_record_run.py`

## Completion Summary
`record_run.py` now computes `duration_s` at write time from `start_ts`/`end_ts` instead of relying on
callers to pass it — no caller currently does, which was silently defeating `generate_retro.py`'s
avg-duration and slow-run sections. The computed value always overrides any caller-supplied
`duration_s`, and degrades to `null` (not an error) when `end_ts` is absent, matching the schema's
documented crashed-run exception. `duration_s` was deliberately left out of `REQUIRED` since it's no
longer a "did the caller remember" field. Historical backfill of the ~552 existing records without
`duration_s` is explicitly out of scope, per the ticket.
