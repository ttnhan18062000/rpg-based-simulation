---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN
phase: open
date: 2026-10-06
tags: [observability, agent-monitoring, process-improvement]
---

# TCK-20261006-HAND-CLOSURE-TIME-SOURCE-DESIGN

## Title
Choose and measure the evidence source and join key that give a hand-closed ticket a real start, end and cost

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST`, with no dependencies. The epic's Request Summary
records why hand closures have `duration_s = 0` and no `cost_proxy_score`:
`record_hand_orchestrated_closure.py` writes `start_ts = end_ts = now`, and nothing links `tools.jsonl` rows to
hand-closure runs. This child decides which evidence to use before any code changes. It measures the candidates
on real data.

## Scope
1. Measure each candidate time source over every hand closure in W40 and W41 (rows with `execution_mode: "hand"`):
   - **A. tools.jsonl session window:** the `tools.jsonl` rows with the closing session's `session_id`, inside a
     window that runs from the ticket's first evidence to the closure call.
   - **B. git:** the first and last commit whose subject cites the ticket ID, plus the time the ticket file
     entered `inprogress/`. Use `git log --follow`.
   - **C. declared:** `--start-ts` passed by the closer. Count how often it is passed today.

   For each, report coverage (the share of hand closures it can date), agreement with the other sources, and
   failure modes. Cover concurrent tickets in one session (the `TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT`
   shape), a ticket spread over several sessions, idle gaps, and squash merges, which leave only the PR title on main.
2. Choose the join key for cost. Either add `session_id` to runs and events, or join by ticket ID and time
   window. State how a `tools.jsonl` row with `run_id: null` is claimed, and how double attribution between
   concurrent tickets is prevented.
3. Write `design.md` in the staging artifacts. It holds the decision, the schema delta (field names, types,
   nullability, and the `duration_source` vocabulary), and the measured table. It also lists the first two
   acceptance criteria for each of children 2-4. Update those child tickets if the decision changes their scope.
4. Frame the owner decision: does a **derived** duration, such as a tool-activity span, count in retro averages,
   or is it shown only beside measured ones? Recommend an answer. The owner decides, and that decision goes
   into Implementation Notes before child 4 starts.

## Out of Scope
- Changing any recorder, hook or retro code. Children 2-4 do that.
- Backfilling past rows (epic Out of Scope).
- Writing transcript token data to `agent-working/agent-monitoring/data/`. `real_token_usage.py` stays local-only.

## Acceptance Criteria
1. `design.md` contains a coverage table with one row per candidate (A/B/C), measured over a named set of hand
   closures with their run_ids, from a stated git ref.
2. One time source and one cost join key are chosen. The rejected options each get a one-line reason.
3. The schema delta is concrete enough for child 2 to implement without further questions.
4. The derived-in-averages question is answered by the owner and quoted in Implementation Notes.
5. Children 2-4 are updated (or confirmed unchanged) to match the decision.

## Related Tickets
- `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST` (parent epic)
- `TCK-20261006-HAND-CLOSURE-RECORDER-REAL-TIMESTAMPS`, `TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION`, `TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE` (siblings)
- `TCK-20260921-HAND-ORCHESTRATION-SIDECAR-STALENESS-INCIDENT`, `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`

## Related Docs
- `docs/agent-monitoring/schema.md` (runs :68-80, tokens :84-86, tools rows :470-480, session_role :664-670)
- `docs/plans/agent_infrastructure/agent_working_direction.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260929-RUN-EXECUTION-MODE-FIELD/`

## Related Code Areas
`tools/agent-monitoring/record_hand_orchestrated_closure.py`, `post_tool_hook.py`, `batch_latency.py`
(git/PR timestamp precedent, "unknown, never zero"), `duration_utils.py`, `real_token_usage.py`.

## Assumptions / Open Questions
- Inferred, not verified per row: closers almost never pass `--start-ts`. Scope 1C measures this.
- If W40-W41 has too few hand closures to judge, extend back to W37 and say so.

## Implementation Notes
Hand-filed by agent-working-design (interim planner) on 2026-10-06. `/create-tickets` could not run its
investigators in this session (see the epic's Implementation Notes), and the owner chose to hand-file.

## Test Summary
(Open.)

## Files Changed
(Open.)

## Completion Summary
(Open.)
