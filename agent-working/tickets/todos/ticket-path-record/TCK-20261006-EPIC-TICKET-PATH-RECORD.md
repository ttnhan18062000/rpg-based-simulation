---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-EPIC-TICKET-PATH-RECORD
phase: open
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-EPIC-TICKET-PATH-RECORD

## Title
Record which path each ticket took, why, and which phases it ran, skipped or left out

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The direction doc row "Record which path each ticket took and why" (idea, "invisible today") is the prerequisite
for the row "Tier-based routing for phases that are almost always skipped". The owner chose it as the next item on
2026-10-06, after the gate override ledger (#369).

**What is already recorded.** `execution_mode` (pipeline|workflow|hand) says *which* path was taken. Nothing says
*why*.

**Phase data is not usable as it stands.** Measured on `origin/main` @ `b15fef405`, W40–W41, 327 runs, 282 of them
`hand`:
- **Standard closures skip phases the tier calls `full`.** `implement-ticket.yaml` marks Investigate, Plan, Review
  and Architecture-Verify as `full` for standard tickets. Yet of 222 standard closures with a Finalize event, only
  43 carry Investigate, 32 Plan, 15 Review and 15 Architecture-Verify. In the rest, the phase has no event at all.
- **The two causes look the same in the data.** A phase that was never logged cannot be told apart from one that
  never ran: hand closures pass a hand-written `--events` list, usually the six-phase hotfix shape.
- **Parity is mostly skipped, with no stated reason.** It is `skipped` in 176 of 210 standard events and 75 of 76
  hotfix events. Whether that means "not applicable" (its `src_change_and_behavior_changed` condition was false) or
  something else is not recorded.

Routing on that data would encode a logging habit, not a working pattern.

## Scope
Two children (see `SEQUENCE.md`):
1. `TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD`. Each run records:
   - `path_reason`;
   - `phases_omitted`, derived from the tier's phase plan in `implement-ticket.yaml`.

   Each skipped event records a `skip_reason`.
2. `TCK-20261006-PATH-AND-PHASE-REPORT-AND-RETRO`: a report-only reading per tier and path showing each phase as
   ran, skipped or omitted, with the reasons, plus a retro section.

## Out of Scope
- Tier-based routing itself, i.e. changing which phases a tier runs. That stays a direction-doc idea until this
  epic's reading exists.
- Backfilling reasons for past runs. They would be invented.
- Making the hand path run more phases. This epic measures; it does not prescribe.

## Acceptance Criteria
1. Both children are DONE.
2. After the first full ISO week following the merge, the retro shows, per tier and path:
   - phase coverage (ran, skipped, omitted);
   - the share of `path_reason` and `skip_reason` that is `unstated`.

   That `unstated` share is the reading's own trust signal.
3. Direction doc: the path-record row moves to `shipped (code)`. The routing row's dependency note points to this
   reading.

## Related Tickets
- `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER` (same recording path; its `PIPELINE-SITES` child is still open)
- `TCK-20261006-EPIC-HAND-CLOSURE-REAL-TIME-AND-COST` (added `execution_mode`, `duration_source`)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md` ("Adaptable" rows)
- `agent-working/agent-orchestration/workflows/implement-ticket.yaml` (per-tier phase plan)
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`, `record_run.py`, `record_events.py`,
  `vocabulary.py`, `generate_retro.py`

## Assumptions / Open Questions
- Both reasons are optional at first and recorded as `unstated` when missing. Making them required would break
  every session's copy of the CLAUDE.md closure command at once. Revisit at the first retro that shows the
  `unstated` share.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06 from origin/main `b15fef405`.

## Test Summary

## Files Changed

## Completion Summary
