---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN
phase: open
date: 2026-10-31
tags: [ai, governance, delivery]
---

# TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN

## Title
The hand/batch path is recorded as the official delivery model, `owner_directed` closes require a `path_note`, and the baseline table is frozen.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Phase 0 (plan section 39). OD-1 is decided yes, so the operating model can be recorded. The baselines are the reference for every later phase.

## Scope
1. Commit the hand/batch model as the official path in `docs/plans/agent_infrastructure/session_layer_working_process.md`, citing #715 6529263880.
2. Define the `path_reason` values in `docs/agent-monitoring/schema.md`, and require `path_note` for `owner_directed` in the recorder's validation. Old rows stay readable.
3. Freeze the baseline table (plan section 46) as a dated, SHA-anchored record, re-measuring only what the plan marks as refreshable. State ubuntu's pre-10-30 host instability: its timings are not a baseline (#715 6527003378).
4. Add a decision record listing each OD as decided or undecided with its date.

## Out of Scope
- Pipeline removal (Phase 4, OD-5).
- Editing CLAUDE.md or settings.json.
- Deciding any open OD.

## Acceptance Criteria
1. The record marks OD-1, 2, 3, 10, 14, 15 as decided with #715 6529263880, and OD-3 as subject to E6b; all others read undecided.
2. A closure with `owner_directed` and no `path_note` is refused, with a test; the other path reasons are unaffected.
3. Each baseline row names its ref and SHA.
4. `tests/tools/` passes in a lead slot.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/session_layer_working_process.md

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
