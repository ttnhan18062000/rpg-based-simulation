# Investigation — TCK-20260915-MONITORING-INTEGRITY-BACKLOG

Every baseline in this ticket's Request Summary was independently re-derived from the real corpus
before implementing anything, per this epic's own established discipline. Two significant
corrections resulted.

## Item 1 — "the gate is red" (root cause corrected)

The ticket text attributed the gate's exit 1 to "19 warnings... Run marked DONE has no working_log
entry." Reading `tools/agent-monitoring/validate.py::main()` directly disproves this: the exit code
is set by `if errors: sys.exit(1)`, which never inspects `warnings`. Warnings are printed but never
gate the exit code, and never have.

Running `make agent-monitoring-validate` today shows the REAL cause: 6 `ERROR: Run with no events`
lines (not mentioned anywhere in the ticket's own text), plus 33 (today; 19 was presumably an
earlier snapshot) `WARNING: Run marked DONE has no working_log entry` lines that do NOT affect the
exit code.

The 6 real "no events" errors, with their own `start_ts`/`ts`/`started_at`:
- `FOLDER-phase40-44-cleanup-authoring` — `ts: 2026-06-10T13:36:00Z`
- `FOLDER-tickets-todos-doc-hardening-` — `started_at: 2026-06-13T10:27:02Z`
- `run-E43B-1782052024` — `start_ts: 2026-06-21T15:00:00Z`
- `FOLDER-tickets/todos/world-data/` — `start_ts: 2026-06-30T18:00:43Z`
- `TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN` — `start_ts: 2026-07-01T17:16:22Z`
- `FOLDER-tickets-todos-simq-corpus-tiers` — `start_ts: 2026-07-06T16:31:17Z`

All 6 are legacy batch (`FOLDER-*`) records or one very early individual-ticket run, all from
2026-06-10 through 2026-07-07 — before `events.jsonl` tracking was consistently wired for every
workflow shape. None can be backfilled (no way to reconstruct real per-phase event data for
completed historical work).

## Item 2 — "34 September closures" (scope corrected: real count is 218, all-time)

Re-derived the ticket's exact query (September-only, TCK-prefixed, DONE, no matching `run_id`) and
got exactly 34, clustered exactly as stated (4/13/14/3 across 09-02 through 09-05) — the ticket's
literal claim is accurate as far as it goes.

But re-running the SAME query with no date restriction beyond `MONITORING_START` (2026-06-07, the
same cutoff `validate.py` already uses) finds **218** working_log rows in this shape, not 34 — the
September cluster is a small, visible fraction of a much larger, older gap the ticket's own
framing ("one hand-orchestrated batch") did not capture.

Checked whether the excess (218 - 34 = 184, plus the September 34 itself) is explained by tickets
closed via an `implement-epic` batch (whose only monitoring coverage lives under the batch's own
`FOLDER-*`/`EPIC-*` run_id, not the individual ticket_id) — a legitimate, non-defective pattern.
Cross-referencing all 218 ticket_ids against every `FOLDER-*`/`EPIC-*` record's own JSON text
(a substring match, not proof) found only ~18 plausible matches. The remaining ~200 are genuinely
unexplained by that hypothesis and, most likely, simply never got a run record written for them —
consistent with `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE`'s own
diagnosis, but showing that gap was far larger and longer-running than the one September cluster
that ticket's own investigation found.

None of the 218 can be backfilled — there is no way to reconstruct an accurate historical
execution record after the fact.

## Item 3 — 9 malformed working_log.csv rows (writer already fixed forward; 9 rows repaired)

Confirmed exactly 9 malformed rows (4 with 7 fields, 2 with 8, 3 with 9) — matches the ticket
exactly. Read all 9 rows' exact raw field lists directly. The cause is confirmed as unescaped
commas — in the title field for most, but in the artifacts_path field for one
(`TCK-20260820-EPIC-WORLD-RENDERING-CORE`, line 1581: `none (epic` / ` scope-only)`), so the
ticket's "cause is the title field" framing was a slight oversimplification, not wrong in the
majority case.

**The writer itself is already safe.** `tools/working_log_writer.py::append_working_log_row`
(introduced by `TCK-20260912-WORKING-LOG-APPEND-HELPER`) uses
`csv.writer(f, quoting=csv.QUOTE_MINIMAL, ...)`, which already quotes any field containing the
delimiter. All 9 malformed rows' timestamps (2026-08-21 through 2026-09-03) predate or are
contemporaneous with that ticket's own introduction (2026-09-12) — they were written by an earlier,
now-removed ad-hoc writer, not by the current sanctioned one. No writer code change was needed;
verified instead with a new explicit regression test using a real comma-bearing title.

**Repair of the 9 existing rows**: in scope per the ticket's own Out-of-Scope wording ("beyond the
9 malformed rows, if repair is chosen at all" implies repairing exactly these 9 is an option).
Manually read each row's exact field boundaries (status is always one of a small known enum:
DONE/EPIC_SCOPED/BLOCKED/INPROGRESS/AMENDED/BACKLOG, and never itself contains a comma) and
reconstructed the correct 6 fields by rejoining the split fragments with `,` (not `, ` — the
original unescaped comma left no extra space, so rejoining with a bare comma reproduces the
original text exactly, byte for byte, modulo the added quoting). Applied via a one-off script that
replaced ONLY those 9 physical lines in place (not a full-file re-serialization, which was tried
first and reverted after it changed the quoting style of ~70 unrelated, already-correct rows).

## Item 4 — 66 runs / 55 events with unusable `ts` (confirmed exact)

Re-derived independently: exactly 66 `runs.jsonl` records (excluding the separately-tracked
`unknown-week` shard) have `start_ts`/`ts` of `None` — 0 have a numeric/epoch value. Exactly 55
`events.jsonl` records have `ts: None`, INCLUDING the 23 such records that live in the
`unknown-week` shard (there are also 5 more events in `unknown-week` with a numeric epoch `ts`,
which the ticket's "55" figure did not separately count, though its prose gestures at that
category existing). All confirmed June-era (W24-W27). Both counts match the ticket exactly once
the shard-inclusion nuance is accounted for.

## Item 5 — `unknown-week/` shard (confirmed exact)

`agent-monitoring/data/unknown-week/`: 5 rows in `runs.jsonl`, 28 in `events.jsonl`, 1 in
`tools.jsonl` — 34 total, matching the ticket exactly.

## Disposition summary

| Item | Disposition |
|---|---|
| 1 | **Fixed.** `validate.py`'s "no events" check now excludes runs starting before 2026-07-08 (the day after the last of the 6 real legacy instances) — the actual, previously-undocumented cause of the permanent redness. Docstring corrected to state warnings never gate the exit code. |
| 2 | **Accept + document + ratchet.** True all-time count is 218, not 34 — corrected and disclosed. Not backfillable. New ratchet check freezes 218. |
| 3 | **Fixed** (writer already safe going forward, proven with a new test) **+ repaired** (9 existing rows corrected in place, minimal 9-line diff). |
| 4 | **Accept + document + ratchet.** Historical, June-era, not backfillable. Ratchet freezes 66/55. |
| 5 | **Accept + document + ratchet.** Directly caused by the same unparseable-`ts` mechanism as item 4. Ratchet freezes 34. |
