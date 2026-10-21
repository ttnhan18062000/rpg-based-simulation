---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261021-HAND-CLOSURE-DURATION-FROM-LAST-ACTIVITY-AND-WEEK-CLOSE-REDERIVE
phase: done
date: 2026-10-21
tags: [agent-monitoring, data-quality, retro]
---

# TCK-20261021-HAND-CLOSURE-DURATION-FROM-LAST-ACTIVITY-AND-WEEK-CLOSE-REDERIVE

## Title
A hand closure made more than 30 minutes after the session's last tool call derives its duration from that last activity block, and week-close re-derives unknown durations from all rows present

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Follow-up from TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH finding 4 (PR #705,
`agent-working/staging_artifacts/TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH/investigation.md` and `unknown_durations.py`).
The owner said yes on 2026-10-21, relayed by lead-planner: file it as a hotfix, agent-working-owned, with no src/ change, and include
the week-close re-derivation.

W43 at `origin/main` has 53 hand-closure run rows. 41 have `duration_source: unknown` (from finding 4):
- 17: the session has no tool rows anywhere. Out of reach here.
- 16: the activity block ending at the closure has fewer than 3 rows. In 10 of them the closure came more than
  `PAUSE_THRESHOLD_SECONDS` (30 min) after the session's last row, so `activity_block()` walking back from the closure finds nothing.
- 4: a back-to-back closure, with fewer than 3 rows after the previous closure. That's correct as is.
- 4: rows reached disk only after the closure. A replay with today's rows derives `tool_activity`.

Two changes in `tools/agent-monitoring/hand_closure_time.py` and `week_close.py` address the 10 and the 4.

## Scope
1. **Anchor to the last activity block (closure time).** In `hand_closure_time.resolve()`, when no `--start-ts` is given and the block ending at the closure time is empty, take the activity block ending at the session's last unattributed row before the closure. Apply the same claim rule (rows after the latest prior closure's end) and the same `MIN_CLAIMED_ROWS`.
   - If it claims at least 3 rows: `duration_source: tool_activity`, `start_ts` = first claimed row, `end_ts` = last claimed row. The work ended at its last tool call. Counting the idle gap up to the closure would inflate the duration, and `duration_s` stays `end - start` as the schema says.
   - Record the real closure time in a new optional run field, `closed_ts`, only when it differs from `end_ts`.
   - A non-empty block ending at the closure keeps today's behaviour exactly.
   - Back-to-back closures are unchanged.
   - `prior_closure_ends` keeps reading `end_ts`. That's correct, because the anchored block ends before the closure.
2. **Week-close re-derivation.** After the existing fold and the main-checkout sweep, `week_close.close_week()` replays `resolve()` for every hand run row of that week with `duration_source: unknown`. The replay uses all of the week's (and the previous week's) tool rows now present, using the run's own `end_ts` (or `closed_ts`) as the closure time.
   - When the replay resolves `tool_activity`, rewrite that run row in place in the canonical `runs.jsonl`: `start_ts`, `end_ts`, `duration_s`, `duration_source`, plus a new optional `duration_rederived: "week_close"`.
   - Leave `declared` and `tool_activity` rows untouched. Don't re-derive cost fields; record that as a limit.
   - Print one line with the number re-derived.
   - Idempotent: a second close changes nothing.
   - **Duplicate hazard (must handle and test):** `run_dedup.py` groups by `(run_id, execution_id, start_ts)`. A re-derived row has a new `start_ts`, so if the old unknown row ever came back it would count as a second run. A later re-close can fold in a late shard that still holds the old row. So the fold for `runs` must drop an unknown row whose `(run_id, execution_id)` matches a row carrying `duration_rederived`. Never drop any other row. Run `duplicate_run_record_check` on the fixture.
3. **Readers: search before changing shape (#699 lesson).**
   - `src/api/agent_ops_dashboard/ingest.py` reads `start_ts`/`end_ts`/`duration_s` and must not break on the new optional keys. Show this with its existing tests (`tests/tools/test_agent_ops_dashboard*.py`).
   - `duckdb_view.py` has a fixed column map: add the two keys or confirm they are ignored.
   - `record_run.validate_record` accepts `closed_ts` (ISO string) and `duration_rederived` (only `"week_close"`).
   - `retro_provenance`: re-derived rows count as `tool_activity`, i.e. derived. The report says how many were re-derived.
   - Grep `src/` and `frontend/` for every field touched, and list the readers in the ticket.
4. **Docs.**
   - `docs/agent-monitoring/schema.md`: the `closed_ts` and `duration_rederived` rows, and the anchored-block rule under `duration_source`.
   - `docs/agent-monitoring/README.md`: a short paragraph on the week-close re-derivation and its limits (cost not re-derived; only finished weeks; the other host's rows only if merged).
   - Update `hand_closure_time.py`'s module docstring.
5. **Tests.**
   - The closure is more than 30 minutes after a block of 5 rows: tool_activity, `end_ts` is the last row, and `closed_ts` is the closure.
   - The same with only 2 rows: unknown.
   - A non-empty current block: unchanged, with today's expected values.
   - Back-to-back: unchanged.
   - Week-close turns an unknown row into tool_activity when late rows exist, and leaves it unknown when they don't.
   - A second close is a no-op.
   - Re-close with a late shard holding the old unknown row: still one run row.
   - Declared and tool_activity rows are untouched.
   - The existing hand_closure_time, week_close, record_hand_orchestrated_closure and dashboard tests pass.
   - Re-run `unknown_durations.py` on W43 and put the before/after split in the Completion Summary.

## Out of Scope
- Changing `MIN_CLAIMED_ROWS`, `PAUSE_THRESHOLD_SECONDS` or the back-to-back claim rule.
- Re-deriving cost (`cost_proxy_score`, `tool_call_count`) at week-close.
- Re-closing W41 or W42. The owner chose no back-fill for them on 2026-10-21. W43 gets the re-derivation at its normal close.
- Any src/ or frontend change. If a reader there needs one, stop and route it to rpg-planner.
- `.claude/settings.json`.

## Acceptance Criteria
- A closure made more than 30 minutes after a block of at least 3 claimable rows records `tool_activity` with the block's span, and `closed_ts` carries the closure time.
- Week-close re-derives unknown hand durations when the rows now allow it. It is idempotent and never duplicates a run, including on a re-close with a late shard.
- The new optional keys are documented and validated, and every src/ and tools/ reader is listed and unbroken.
- The tests above pass. The W43 before/after split is recorded. REGISTRY is regenerated after the last docs edit.

## Related Tickets
- TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH (finding 4; PR #705)
- TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS and TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN (the derivation being changed)
- TCK-20261020-HAND-CLOSURE-AGENT-COUNT-UNKNOWN (#699; the src-reader lesson)

## Related Docs
- docs/agent-monitoring/schema.md, docs/agent-monitoring/README.md
- agent-working/agent-monitoring/retro/RETRO-2026-W43.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN/ (design.md)
- agent-working/stored_artifacts/TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH/ (after #705 merges)

## Related Code Areas
- tools/agent-monitoring/hand_closure_time.py (`activity_block`, `claim_rows`, `resolve`, `resolve_for_session`)
- tools/agent-monitoring/week_close.py (`close_week`, `_fold_kind` for runs), run_dedup.py, record_run.py, retro_provenance.py, duckdb_view.py
- tools/agent-monitoring/record_hand_orchestrated_closure.py (writes `closed_ts`)
- src/api/agent_ops_dashboard/ingest.py (reader only; no edit)

## Assumptions / Open Questions
- **`end_ts` meaning.** Setting `end_ts` to the last tool call for the anchored case means "work ended", not "recorded". `closed_ts` keeps the recording time, so nothing is lost. If a reader turns out to rely on `end_ts` being the closure time, keep `end_ts` and stop to ask instead of inventing a third shape.
- **Depends on #705.** Base this on origin/main after #705 merges, or merge it in when it lands. The sweep runs before the re-derivation.

## Implementation Notes
- 2026-10-20 (agent-working-planner): owner yes (via lead-planner). Batch 9.
- 2026-10-21 (agent-working-implementer): **Readers of the touched fields** (searched `src/`, `frontend/`, `dashboard-frontend/` and `tools/`; no src/ or frontend edit needed):
  - `src/api/agent_ops_dashboard/ingest.py` (lines ~287, 401-403) builds `RunSummary`/run dicts from explicit `start_ts`, `end_ts`, `duration_s` reads, never `**record`; the new keys are ignored. `models.py` pydantic models use default extra handling. Dashboard stats/api tests pass (see Test Summary).
  - `dashboard-frontend/src/api.ts` mirrors those three fields only.
  - `tools/agent-monitoring/duckdb_view.py`: fixed column map, "anything else in a record is ignored" (confirmed in its comment); `closed_ts`/`duration_rederived` are not added.
  - `tools/agent-monitoring/duration_utils.py` (`compute_active_idle_split`): **needed a change.** Hand-closure events are stamped with the recording time, which is after an anchored `end_ts`; counting them made the wait up to the recording one idle gap larger than the run. Events after `end_ts` are now skipped (test added).
  - `validate.py` (end_ts present/absent only), `build_index.py`, `legacy_reader.py`, `read_ranged_baseline.py`, `generate_retro.py`: read `end_ts`/`duration_s` as values; unaffected.
  - `retro_provenance.py`: re-derived rows are `tool_activity`; the hand-coverage line now says how many were re-derived.
  - `run_dedup.py`/`duplicate_run_record_check.py`: group on `(run_id, execution_id, start_ts)`; handled by dropping the stale unknown row at the re-close (tested with both).
- `end_ts` for the anchored case is the last tool call; no reader relied on it being the closure time.

## Test Summary
New: test_hand_closure_time.py (9: anchored five rows with `closed_ts`, two rows unknown, non-empty block unchanged, back-to-back unchanged, claim after previous closure, declared never anchors, field validation, CLI end to end, duration_utils clamp); test_week_close_rederive_durations.py (9: re-derive and mark, idempotent, too few rows untouched, late shard and previous week, declared/tool_activity/other-session/non-hand untouched, later closure claims after the re-derived end, re-close with a late shard holding the old unknown row keeps one run and passes `check_duplicate_run_records` with ceiling 0, CLI line); test_retro_provenance.py (1). Passing unchanged: dashboard stats and api tests, generate_retro, record_run, record_hand_orchestrated_closure, week_close (4 files), hand_closure_time. No full tests/tools run.

## Files Changed
- tools/agent-monitoring/hand_closure_time.py (`Resolution.closed_ts`, `_anchored`, `resolve`, docstring)
- tools/agent-monitoring/record_hand_orchestrated_closure.py (writes `closed_ts`), record_run.py (validates `closed_ts`, `duration_rederived`)
- tools/agent-monitoring/week_close.py (`rederive_week_durations`, `close_week`, CLI line)
- tools/agent-monitoring/duration_utils.py (events after `end_ts` skipped), retro_provenance.py (re-derived count)
- docs/agent-monitoring/schema.md, README.md
- tests/tools/test_hand_closure_time.py, test_week_close_rederive_durations.py, test_retro_provenance.py

## Completion Summary
A hand closure made more than 30 minutes after the session's last tool call now derives from that last activity block (`tool_activity`, `end_ts` = last claimed row, `closed_ts` = the closure), and a week close re-derives `unknown` hand durations from the rows then present, marks them `duration_rederived: "week_close"`, and drops a stale unknown row a late shard brings back. Re-run on a scratch copy of W42-W43 from `origin/main` plus the main checkout's restored `main.tools.jsonl` (W43 hand run rows): **before** 19 `tool_activity` / 43 `unknown`; **after one close** 30 `tool_activity` (11 re-derived) / 32 `unknown`, 1404 rows swept; a second close changed nothing. The remaining unknowns are the ones with no rows at all, too few rows, or true back-to-back closures (unchanged rules). No src/ or frontend change.
