---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP
phase: done
date: 2026-09-06
tags: [agent-monitoring, data-quality]
---

# TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP

## Title
`record_hand_orchestrated_closure.py` writes false `0`/`0.0` stats (should be absent) and never appends `tickets/working_log.csv`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
User-observed anomaly: some `agent-monitoring/data/YYYY-Www/events.jsonl` records show
`tool_call_count: 0` / `cost_proxy_score: 0.0` for every phase of a run, which reads as
suspicious. Investigation traced this to `record_hand_orchestrated_closure.py` (built by
`TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE`, already closed — that
ticket's scope was only "does a run get recorded at all," not "are the derived stats fields
correct"). Root cause is two independent, narrow bugs in that one script:

1. **False zero instead of null.** `record_events.compute_tool_stats()` (line ~74) is correct by
   design for its original caller (`record_events.py`'s own CLI, used by real
   `implement-ticket.js` phases): for `implement-ticket`-workflow run_ids, a phase genuinely
   having zero matching `tools.jsonl` rows means "confirmed zero tool calls," because those
   phases always have a live `.claude/current_run` sidecar during the real work
   (`test_cost_proxy_score_absent_when_no_tools_jsonl_exists` pins this as intentional).
   `record_hand_orchestrated_closure.py` reuses this same function for synthetic, after-the-fact
   event records — but a hand-orchestrating session never writes a live per-phase sidecar during
   the actual work (this exact gap was already found and only partially mitigated by
   `TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP`'s advisory-only nudge). So "zero
   matching rows" for a hand-orchestrated closure means "no attribution data was ever possible,"
   not "confirmed zero calls" — yet the script writes the same `(0, 0.0)` either way, silently
   destroying the null/unattributed signal `docs/agent-monitoring/schema.md` already documents
   for other zero-sidecar workflows (`implement-epic`, `create-tickets`).
   Confirmed live and ongoing: 21 of 108 unique runs in `agent-monitoring/data/2026-W36/` show
   100%-zero stats across every phase, dated 2026-09-03 through 2026-09-06 (today).
2. **`tickets/working_log.csv` is never appended.** `record_hand_orchestrated_closure.py` has no
   reference to `working_log.csv` at all (confirmed via grep), even though CLAUDE.md's own "After
   Work" checklist requires every closed ticket to append a row there, and
   `tools/validate_working_log.py` / `tools/agent-monitoring/validate.py` both check for it.
   Nearly every ticket closed via this wrapper in the last few days is missing its entry.

## Scope
- Add an opt-in `omit_when_unattributed: bool = False` parameter to
  `record_events.compute_tool_stats()` (default preserves existing, tested, correct behavior for
  the real `implement-ticket.js`/`record_events.py` CLI path) — when `True`, keys with zero
  matching `tools.jsonl` rows are omitted from the returned dict entirely, rather than mapped to
  `(0, 0.0)`.
- `record_hand_orchestrated_closure.py` passes `omit_when_unattributed=True`. Its existing
  `if key in tool_stats:` loop already does the right thing once the dict correctly omits
  unattributed keys — no further change needed there.
- Add `--title` and `--log-summary` (required) plus `--artifacts-path` (optional, defaulted the
  same way `implement-ticket.js`'s own Finalize prose already computes it: `stored_artifacts/
  <ticket-id>` for standard/epic tier, `none (hotfix — no staging artifacts)` for hotfix) CLI
  arguments, and append one row to `tickets/working_log.csv` (via Python's `csv` module,
  `QUOTE_MINIMAL`, matching the existing header `timestamp,ticket_id,title,status,summary,
  artifacts_path`) after a successful run/event write.
- Update `docs/agent-monitoring/README.md`'s "Recording coverage for a hand-orchestrated closure"
  subsection: the new required args, and that `working_log.csv` is now appended automatically —
  a hand-orchestrating session should stop appending it manually when using this wrapper, to
  avoid duplicate rows.
- Update `docs/agent-monitoring/schema.md` to note this specific nuance: `tool_call_count`/
  `cost_proxy_score` being absent for a `TCK-`-prefixed (implement-ticket-classified) run_id can
  now legitimately mean "hand-orchestrated closure with no live sidecar," not only "predates the
  field" or "non-implement-ticket workflow."
- Explicit decision, per user instruction: do **not** backfill/correct the historical rows already
  written with false `(0, 0.0)` — matches this repo's own established precedent
  (`TCK-20260807-...`'s and `TCK-20260903-...`'s Completion Summaries both explicitly decline to
  backfill historical data on the same reasoning: fabricating retroactive certainty about
  unattributed history is worse than an honestly-labeled historical gap). Only future writes via
  this script get the fix.

## Out of Scope
- Building a real live-sidecar-during-hand-orchestration mechanism — structurally not applicable;
  hand orchestration by definition skips the phase machinery a sidecar would attribute to. That
  gap is `workflow_reliability_epic.md`'s M1 (session-scoping the sidecar path for its two real
  consumers), a different problem already tracked there.
- Backfilling/correcting historical `(0, 0.0)` events.jsonl rows or historical missing
  `working_log.csv` rows — explicitly declined per the Scope section above.
- Any change to `record_events.py`'s own CLI-invoked default behavior for real
  `implement-ticket.js` runs — that path's `(0, 0.0)` semantics are correct and unchanged.
- A done-checker/hook gate enforcing hand-orchestrated coverage — `TCK-20260903-...` already made
  and documented this exact "not now, deliberate boundary" call; not revisited here.

## Acceptance Criteria
- [x] `compute_tool_stats(records, omit_when_unattributed=True)` omits `(run_id, seq)` keys with
      zero matching `tools.jsonl` rows from its returned dict; default (`False`) behavior is
      unchanged (existing tests still pass unmodified).
- [x] `record_hand_orchestrated_closure.py` event records for unattributed phases have no
      `tool_call_count`/`cost_proxy_score` keys at all (verified via a new test).
- [x] `record_hand_orchestrated_closure.py` appends a correctly-quoted row to
      `tickets/working_log.csv` after a successful write (verified via a new test, including a
      summary containing an embedded comma round-tripping correctly).
- [x] `docs/agent-monitoring/README.md` and `docs/agent-monitoring/schema.md` updated to reflect
      both fixes.
- [x] Historical data explicitly left as-is (documented decision, not silently omitted).

## Related Tickets
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (done) — built the wrapper
  this ticket fixes; that ticket's scope was existence of coverage, not correctness of stats or
  the working_log append.
- `TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP` (done) — established the "advisory
  nudge alone doesn't fix hand-orchestration sidecar gaps" precedent and the "don't backfill
  history" precedent this ticket follows.
- `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` (done) — an earlier, differently-caused
  false-zero stats bug; same field, different root cause.

## Related Docs
- `docs/agent-monitoring/schema.md`
- `docs/agent-monitoring/README.md`

## Related Stored Artifacts
None — hotfix tier, no staging artifacts.

## Related Code Areas
- `tools/agent-monitoring/record_events.py::compute_tool_stats()`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tests/tools/test_record_events.py`
- `tests/tools/test_record_hand_orchestrated_closure.py`

## Assumptions / Open Questions
None — root cause fully traced and confirmed via direct code read and a live interpreter
reproduction before this ticket was filed.

## Implementation Notes
Confirmed via a direct interpreter reproduction that `compute_tool_stats()` returns `(0, 0.0)` —
not an absent key — for every `(run_id, seq)` in its `wanted` set, including ones with zero
matching `tools.jsonl` rows (`{key: (...) for key in wanted}`, no filter). Confirmed this is
*intentional and correctly tested* for `record_events.py`'s own CLI path
(`test_cost_proxy_score_absent_when_no_tools_jsonl_exists`), so the fix could not live in
`compute_tool_stats()`'s default behavior without breaking that real contract. Added an opt-in
`omit_when_unattributed` parameter instead (default `False`, zero change to any existing caller)
and had only `record_hand_orchestrated_closure.py` — the one caller whose events never have a live
sidecar during the real work — opt in. Its existing `if key in tool_stats:` loop already did the
right thing once the dict correctly omits unattributed keys; no further change was needed there.

Separately confirmed via `grep` that `record_hand_orchestrated_closure.py` never referenced
`tickets/working_log.csv` at all. Added `--title`/`--log-summary` (required) and
`--artifacts-path` (optional, defaulted the same way `implement-ticket.js`'s own Finalize prose
computes it) CLI args, and a `csv.writer(..., quoting=csv.QUOTE_MINIMAL)` append after a
successful run/event write — non-fatal on failure (warns to stderr), matching this repo's
"monitoring write failure must never fail the workflow" rule.

Decided not to backfill either historical gap (false `(0, 0.0)` stats, or missing `working_log.csv`
rows) for events/tickets already recorded via this script before this fix — matches
`TCK-20260807-...`'s and `TCK-20260903-...`'s own established precedent (fabricating retroactive
certainty about unattributed history is worse than an honestly-labeled gap); this is a
go-forward-only fix, per explicit user instruction.

## Test Summary
- `pytest tests/tools/test_record_events.py -v` — 27 passed, including 3 new tests for
  `omit_when_unattributed`: default behavior unchanged, true omits zero-match keys, true still
  computes real matches correctly for a mixed batch.
- `pytest tests/tools/test_record_hand_orchestrated_closure.py -v` — 22 passed: all 5 pre-existing
  CLI tests updated to pass the new required `--title`/`--log-summary` args (regression-checked,
  no behavior change); 2 new tests confirming unattributed phases get no `tool_call_count`/
  `cost_proxy_score` keys while a real attributed seq still computes correctly; 6 new tests
  covering `working_log.csv` append (correct columns, tier-based artifacts-path default, explicit
  override, embedded-comma round-trip via `csv.reader`, missing-title rejection with no partial
  write, and non-fatal warning when the working_log parent dir doesn't exist).
- `pytest tests/tools/test_record_events.py tests/tools/test_record_run.py
  tests/tools/test_record_hand_orchestrated_closure.py
  tests/tools/test_done_ticket_monitoring_coverage.py -q` — 85 passed, confirming no regression in
  any sibling monitoring tool.
- `python3 tools/validate_frontmatter.py <each changed doc/ticket> --content-type {doc,ticket}` —
  OK for `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`, and this ticket.

## Files Changed
- `tools/agent-monitoring/record_events.py` — added opt-in `omit_when_unattributed` parameter to
  `compute_tool_stats()`.
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` — passes
  `omit_when_unattributed=True`; added `--title`/`--log-summary`/`--artifacts-path` args and the
  `tickets/working_log.csv` append; updated module docstring.
- `tests/tools/test_record_events.py` — 3 new tests.
- `tests/tools/test_record_hand_orchestrated_closure.py` — 5 existing CLI tests updated for the
  new required args; 8 new tests.
- `docs/agent-monitoring/README.md` — updated the hand-orchestrated-closure recording section.
- `docs/agent-monitoring/schema.md` — added the hand-orchestrated-closure nuance to "How tool
  calls are attributed to agent events".

## Completion Summary
Root-caused and fixed two independent, narrow bugs in
`tools/agent-monitoring/record_hand_orchestrated_closure.py`, both confirmed live and ongoing (not
historical scar tissue): (1) it wrote a false `(0, 0.0)` instead of omitting `tool_call_count`/
`cost_proxy_score` for phases that never had a live sidecar during hand-orchestrated work, by
reusing a shared function's assumption that only correctly holds for real `implement-ticket.js`
runs; (2) it never appended to `tickets/working_log.csv` at all, despite that being a documented
CLAUDE.md requirement. Both are fixed going forward via a minimal, backward-compatible opt-in
parameter and a new non-fatal CSV append; the shared `compute_tool_stats()` function's default,
tested behavior for real workflow runs is unchanged. Historical false-zero events and missing
working_log rows are explicitly not backfilled, per repo precedent and explicit user instruction.
Both docs (`README.md`, `schema.md`) updated to document the fix and warn against double-appending
`working_log.csv` when using the wrapper.
