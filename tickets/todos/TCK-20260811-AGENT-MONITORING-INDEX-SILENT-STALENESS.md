---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS
phase: open
date: 2026-08-11
tags: [observability]
---

# TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS

## Title
`generate_retro.py`'s derived SQLite index degrades silently when stale (present but outdated),
under-reporting retro numbers with no warning

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found while running `/agent-monitoring-retro` at the end of a long session
(2026-08-10/11, `RETRO-2026-W33.md`). `tools/agent-monitoring/generate_retro.py`'s
`_load_runs_and_events()` reads from `agent-monitoring-index/monitoring.db` (built by
`tools/agent-monitoring/build_index.py`) instead of scanning `agent-monitoring/runs.jsonl`/
`events.jsonl` directly, and only rebuilds the index on demand if the DB file is **missing**
(`if not DEFAULT_DB_PATH.exists(): ... build_index.build(...)`) — never if it's merely stale.

In this session, the index was last built at `2026-08-10T14:15+07`, before the first ticket of a
5-ticket batch even closed. The retro run at `2026-08-10T19:15+07` (~5 hours later, `runs.jsonl`
mtime `2026-08-11T02:14+07` local) silently used the stale index and reported **7 runs / 41
events** for the week — a 61% under-count versus the real, correct **18 runs / 123 events**
confirmed after a manual rebuild. Every gate-failure entry, most DONE tickets, and both
`architecture_violation`/`documentation_accuracy` reason codes from that session's work were
invisible in the first (stale-index) report. No warning, error, or staleness indicator was printed
— the report looked complete and plausible.

This is a real risk for anyone trusting `/agent-monitoring-retro`'s numbers at face value, per this
skill's own stated purpose ("Before trusting the numbers, cross-check integrity" — currently the
only documented mitigation is `make agent-monitoring-validate`, which does NOT check index
freshness, only cross-file consistency of the JSONL sources themselves).

## Scope
- Add a staleness check to `_load_runs_and_events()` (`tools/agent-monitoring/generate_retro.py`):
  compare `DEFAULT_DB_PATH`'s mtime against `RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_TOOLS_FILE`'s mtimes;
  if any source file is newer than the index, rebuild before reading (same code path already used
  for the missing-index case) rather than silently reading stale data
- Alternatively/additionally: have `record_run.py`/`record_events.py` touch or invalidate the index
  file on every write, so the index is never more than one retro-run stale regardless of what reads
  it
- Whichever mechanism is chosen, it must not become a hard gating dependency (same constraint the
  existing code comment already states for the missing-index case) — a rebuild failure should
  degrade to the direct JSONL scan fallback that already exists, not raise
- Add a regression test: write a JSONL row, confirm a stale (pre-existing, older) index file gets
  rebuilt before the row is reflected in retro output

## Out of Scope
- `make agent-monitoring-validate`'s own cross-file consistency checks — unrelated, already working
  correctly (confirmed this session: it flagged real, pre-existing, unrelated June-2026 tickets
  missing `working_log.csv` entries, nothing caused by index staleness)
- Any change to `query.py`'s or `validate.py`'s own `open_index()` (which hard-fails on a missing
  index, unlike `generate_retro.py`'s soft-degrade) — different failure mode, not this ticket's scope

## Acceptance Criteria
- [ ] `generate_retro.py` detects a stale-but-present index (any source JSONL newer than the DB
      file) and rebuilds before reading, not just when the DB file is missing
- [ ] Rebuild failure degrades to the existing direct-JSONL-scan fallback, does not raise
- [ ] New regression test confirms a stale index gets rebuilt and the retro output reflects a
      freshly-written record that predates the stale index but postdates the source JSONL write
- [ ] `docs/guides/agent_monitoring.md` (or wherever this skill's own doc lives) is updated to state
      staleness is now handled automatically, if the doc currently implies manual rebuild is needed

## Related Tickets
None yet.

## Related Docs
- docs/guides/agent_monitoring.md (if it exists — confirm path at Implement time)
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py (`_load_runs_and_events()`)
- tools/agent-monitoring/build_index.py

## Assumptions / Open Questions
- Whether a periodic/hook-based touch-on-write approach (record_run.py/record_events.py
  invalidating the index) is preferable to a staleness-check-on-read approach in generate_retro.py,
  or both should coexist as defense in depth — not decided here, an Implement-time design call

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
