---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261031-RETRO-SAYS-MID-WEEK-UNKNOWN-DURATIONS-DERIVE-AT-WEEK-CLOSE
phase: done
date: 2026-10-31
tags: [agent-monitoring, data-quality]
---

# TCK-20261031-RETRO-SAYS-MID-WEEK-UNKNOWN-DURATIONS-DERIVE-AT-WEEK-CLOSE

## Title
Retro Run Summary: for a week that isn't closed yet, say that its unknown hand-closure durations are derived at the week close

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
This is proposal 5 of the W44 retro (PR #804, `agent-working/agent-monitoring/retro/RETRO-2026-W44.md`). The owner said
"Yes, triage them" (#715 issuecomment-6545824938 item 2), and agent-working-planner-u24 triaged it to this hotfix.

The W44 report, generated mid-week, shows `Avg duration (measured/declared, n=0) | n/a (unknown, not averaged: 26)`.
26 of its 72 hand closures look like they have no duration recorded. They do have one: `week_close.py::rederive_week_durations`
gives them a tool-activity duration when the week is closed. The W41 close in #804 did exactly that for one such row
(None -> 262 s). A reader can't tell "not derived yet" from "never recordable".

## Scope
- `tools/agent-monitoring/retro_provenance.py` (the Run Summary rows / provenance note) and, if the per-week table needs it,
  `tools/agent-monitoring/generate_retro.py` (l.~1491): when the report covers an ISO week that still has unconsolidated
  shards, or one that isn't finished, add one sentence beside the unknown count. It says that unknown hand-closure
  durations get a derived duration at `make agent-monitoring-close-week`. A closed week's report doesn't change.
- Decide "week not closed yet" from data the generator already reads, either per-identifier shards present or week not
  finished per `week_close.is_finished`. Say which in the PR. Don't add a new state file.
- Tests in `tests/tools/` (e.g. next to `test_retro_provenance.py`): an open week gets the sentence, and a closed week
  with no shards doesn't.

## Out of Scope
- Changing which rows are averaged or how durations are derived.
- LAST7D/LAST28D/ALL rolling reports, unless they share the same row function. If they do, say in the PR what they
  show.
- Regenerating already-committed retro reports.

## Acceptance Criteria
1. A report for an unclosed week carries the sentence next to the unknown count. A report for a closed week is
   byte-identical to before for that row.
2. The new tests pass, and so does `pytest tests/tools -k "retro" -p no:randomly`.
3. The PR body quotes the before and after Run Summary line.

## Related Tickets
- TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE (built the provenance rows)
- TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND (week_close.py)

## Related Docs
- docs/guides/agent_monitoring.md ("How to Generate a Report")

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/retro_provenance.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/week_close.py (read only)

## Assumptions / Open Questions
- None open. Dispatch: hotfix. It's agent-working-planner-u24's to dispatch only with an owner go through lead-planner-u24.

## Implementation Notes
- Dispatched by agent-working-planner-u24 (S4, noted in #715 6545962757).
- "Week not closed yet" is `not week_close.is_finished(week_str, date.today())`: the week has not ended. It uses no new state and no shard scan. A finished week that is not closed yet is not covered; the dispatch asked for one signal and this is the cheaper and deterministic one.
- `retro_provenance.run_summary_rows(p, week_open=False)` appends "; the week is not finished, so these get a derived duration at `make agent-monitoring-close-week`" inside the unknown count's parentheses, only when the week is open and the unknown count is above 0. `generate()` takes a new `week_open=False` argument, set by `main()` through `_week_is_open()` (False for `--all`/`--days` rolling windows, an unreadable week id, or any error).
- The LAST7D/LAST28D/ALL reports share the same row function but pass no week, so they are unchanged. Already-committed reports are not regenerated.

## Test Summary
- `pytest tests/tools -k "hand_orchestrated or retro or closure or path_report" -p no:randomly` (serial): 416 passed. New tests in `test_retro_provenance.py`: an open week gets the sentence once, a closed week is byte-identical, no unknowns adds nothing, `_week_is_open` against a pinned date.

## Files Changed
- tools/agent-monitoring/retro_provenance.py, tools/agent-monitoring/generate_retro.py
- tests/tools/test_retro_provenance.py

## Completion Summary
AC1 met: an open week's Run Summary row carries the sentence next to the unknown count, and a closed week's row is byte-identical (default and explicit `week_open=False` compare equal). AC2: the new tests and the retro tests pass. AC3: the PR body quotes the before and after line.
