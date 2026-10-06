---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST
phase: open
date: 2026-10-06
tags: [observability, agent-monitoring, process-improvement]
---

# TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST

## Title
Epic: record real time and cost for hand-closed tickets, with stated provenance, or record them as unknown, never as zero

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/agent_infrastructure/agent_working_direction.md` (Observable) lists "Real time and cost for
hand-closed work" as an idea. The W40 retro measured the problem: about 94% of runs since early September are
hand closures with zero duration, and the spend proxy covers 18.3% of events (77 of 420). On 2026-10-06 the
owner picked this as the next agent-working direction. The direction doc says it "changes how every later retro
reads, so it needs its own design", so this epic puts a design child first.

Facts gathered from `origin/main` (`40ab9857e`) on 2026-10-06. RHC = `tools/agent-monitoring/record_hand_orchestrated_closure.py`.
- **Why duration is 0.** RHC sets `now` once and writes `start_ts = end_ts = now` unless `--start-ts` or `--end-ts`
  is passed (RHC:196, 204-205, 363-364). It sets every event's `ts` to `now` too (RHC:224). Its docstring calls
  identical timestamps a deliberate precedent "when real elapsed wall-clock time wasn't tracked" (RHC:29-31).
  `duration_s = end - start` therefore comes out 0.
- **Why the retro hides it.** The retro's Avg duration counts only truthy `duration_s`
  (`generate_retro.py:798-800`). Zero-duration hand runs are left out silently, and the hand-closed mode shows "n/a".
  A recorded 0 here means "unknown". It is not a measurement.
- **Why cost is missing.** `cost_proxy_score` is attached only when `tools.jsonl` rows carry the event's
  `(run_id, seq)` from a live sidecar (RHC:433-438). Hand closures have none, so the key is left out by design
  (`TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP`).
- **Evidence that exists but is not joined.**
  - (a) Every `tools.jsonl` row has `session_id`, `ts` and `duration_ms` (`post_tool_hook.py:73-174`), and rows
    without a sidecar get `run_id: null`. Runs and events carry no `session_id` (schema.md:68-80), so nothing joins them.
  - (b) `real_token_usage.py` reads Claude Code transcripts (`message.usage`). It works only on the local
    machine, is day-grained, has no ticket key, and is never written to the data folder (schema.md:86).
  - (c) `batch_latency.py` derives per-PR timings from commit and PR timestamps; it marks missing values
    "unknown", never zero.
  - (d) Git commits that reference the ticket ID (the commit convention). Only one `Claude-Session:` trailer
    exists in all of history, so that trailer cannot serve as evidence.
- **What we already have.** `execution_mode: "hand"` (`TCK-20260929-RUN-EXECUTION-MODE-FIELD`) separates hand
  closures from pipeline runs for new rows. Older rows are "unlabelled" and are not backfilled.

## Scope
Children, in order. `/create-tickets` files them after the owner accepts the design child's decision.
1. **Design (standard):** choose the time source and join key for a hand closure, and measure them on real
   W40/W41 data before choosing. Candidates:
   - `tools.jsonl` rows whose `session_id` matches the closing session, within a window bounded by the ticket's
     first evidence (its move to `inprogress/` or first ticket-ID commit) and the closure call.
   - Git commit timestamps that reference the ticket ID.
   - An explicit start passed by the closer: RHC already accepts `--start-ts`.

   For each candidate, report its coverage on recent hand closures and its failure modes: concurrent tickets in
   one session (the `TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT` shape), a ticket spread over
   several sessions, and idle gaps. Output: a decision, a schema delta, and the first two acceptance criteria
   of each later child.
2. **Recorder (standard):** RHC records real `start_ts`/`end_ts` from the chosen source. It adds a provenance
   field, e.g. `duration_source: declared | derived_tools | derived_git | unknown`. When no source qualifies,
   `duration_s` is null, not 0. Event `ts` values come from evidence where it exists. Stamp `session_id` on
   runs and events (the missing join key) if the design chooses it.
3. **Cost attribution (standard):** for hand closures, attribute the joined `tools.jsonl` rows so that
   `cost_proxy_score` and `tool_call_count` are filled, with a provenance marker. Keys stay absent when nothing
   joins, as today.
4. **Retro (standard):** show durations and costs per provenance and never mix derived values into measured
   averages without a label. Update the coverage note. State in the retro which tables change meaning from the
   week this lands, at minimum: Avg duration, per-mode avg, Slow Runs, duration outliers, the active/idle split,
   Spend Proxy by Phase/Agent and cost outliers.

## Out of Scope
- **Backfilling historical rows.** A derived duration written into past shards would be invented history (the
  same reasoning as the integrity report's "7 epics with no working_log row"). A read-only, labelled
  retrospective estimate in a report is acceptable only if the design child asks for one.
- Writing transcript token counts into `agent-working/agent-monitoring/data/`. They stay local-only (schema.md:86).
- Any blocking gate over monitoring data (direction-doc rule: advisory only). Monitoring write failure never
  fails the workflow.
- Changing `cost_proxy.py`'s formula.

## Acceptance Criteria
1. Every child is closed or explicitly dropped with an owner-recorded reason.
2. On the first full ISO week after child 4 lands, the retro reports, for hand-closed runs, the share with
   non-null duration and the share with a cost value, each split by provenance. No hand-closed run reports
   `duration_s: 0` unless its evidence really spans zero seconds.
3. A hand closure with no qualifying evidence records `duration_source: unknown` and null duration. A test
   pins this.
4. `agent_working_direction.md`'s row for this direction moves to `shipped` with the measured coverage.

## Related Tickets
- Children (order in `SEQUENCE.md`): `TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN`,
  `TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS`, `TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION`,
  `TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE`
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (built RHC)
- `TCK-20260906-HAND-ORCHESTRATED-CLOSURE-STATS-AND-LOG-GAP` (absent keys, not false zeros)
- `TCK-20260929-RUN-EXECUTION-MODE-FIELD` (the `execution_mode` split; chose not to infer hand from zero duration)
- `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`, `TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE`
- `TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT` (misattribution risk for any session/time join)
- `TCK-20260809-MONITORING-ZERO-DURATION-COMBAT-RUNS-HOTFIX`, `TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG`
- `TCK-20261002-EPIC-SESSION-LAYER-MEASUREMENT-AND-REVIEW` (M7 reads the same data; coordinate any schema change)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md`
- `docs/agent-monitoring/schema.md`
- `agent-working/agent-monitoring/RETRO-2026-W40.md` (W40 retro; coverage line at :110, hand-closure note at :344-346)

## Related Stored Artifacts
None yet.

## Related Code Areas
`tools/agent-monitoring/record_hand_orchestrated_closure.py`, `record_run.py`, `record_events.py`,
`post_tool_hook.py`, `cost_proxy.py`, `duration_utils.py`, `generate_retro.py`, `batch_latency.py`,
`real_token_usage.py`.

## Assumptions / Open Questions
- **Owner decision at the design child:** whether a derived duration, such as a span of tool activity, counts
  as "real time" for averages, or is only reported beside measured durations. The design child recommends; the
  owner decides.
- Session-layer M7 (not before about 2026-11-02) consumes runs and events. If the design adds `session_id` to
  runs and events, check that M7's metrics are unaffected, or fold the change into M7's evidence.
- Inferred, not verified per row: hand closers almost never pass `--start-ts`. The design child measures this.

## Implementation Notes
2026-10-06, agent-working-implementer: all four children are closed in `agent-working/tickets/done/` (design, recorder, cost attribution, retro). AC3 is pinned by `tests/tools/test_hand_closure_time.py`; the direction-doc row is moved to "shipped (code)" with the baseline coverage. **The epic stays open for AC2 and the measured part of AC4:** the first full ISO week after the PR merges must show, for hand-closed runs, the share with a duration and with a cost value per provenance (the retro prints this in "Hand-closed runs by duration source"). Expected ceiling from the design: about 55% duration coverage, because many sessions write no tools rows (`TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES`).

Drafted by agent-working-design (interim planner), 2026-10-06, after the owner picked this direction. The facts
come from a read-only sweep of `origin/main` at `40ab9857e`.

The owner said "proceed" with `/create-tickets`. The Workflow run `wf_4a572e02-40e`, from `7570beb90`, returned
`NOTHING_TO_CREATE` ("all concerns are already covered") with no duplicates listed. In fact all 4
`concern-investigator` agents failed with "agent type not found": this session was launched from the parent
directory, so the repo's project agents were not loaded. That false all-clear is filed as
`TCK-20261006-CREATE-TICKETS-FAILED-INVESTIGATIONS-REPORTED-AS-COVERED`. The owner then chose to hand-file the
children, and design wrote them from the same facts. The run's own monitoring rows (status `NOTHING_TO_CREATE`)
stay in the shard as a true record of what the run reported.

## Test Summary
(Epic: none.)

## Files Changed
(Open.)

## Completion Summary
(Open.)
