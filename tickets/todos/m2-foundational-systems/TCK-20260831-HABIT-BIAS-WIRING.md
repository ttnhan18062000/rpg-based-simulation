---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260831-HABIT-BIAS-WIRING
phase: open
date: 2026-08-31
tags: [cognition]
---

# TCK-20260831-HABIT-BIAS-WIRING

## Title
Wire the existing HabitBiasService into ActionStyle bias (Earned Habits)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Earned Habits & Behavioral Tendencies. Investigation found the atlas card's premise ("no existing accumulation scaffolding") is factually outdated — HabitMemory and HabitBiasService already implement gradual-accumulation habit bias (±0.1 per outcome, bounded [0,1]) from the archived Phase 16 Emotion/Recovery/Habit domain, but have zero production call sites. It's cheaper and lower-risk to wire this existing service into the already-precedented ActionStyle bias point than to build a new mechanism as the atlas assumed.

## Scope
- Correct the atlas's "no scaffolding" premise in the ticket and scope this as wiring the existing HabitBiasService, not building new accumulation state.
- Add at least one real production consumer of HabitBiasService.apply_habit_bias at the ActionStyle bias point (src/content_semantics/personality.py's get_action_style_for_bravery), closing the current zero-call-site gap.
- Gate the mechanism behind a FeatureMode flag, default OFF.
- Apply habit-accumulation state changes only through the authoritative apply path; keep PersonalityComponent frozen/immutable.
- Make an explicit choice between gradual-accumulation-only vs. also supporting discrete milestone-event marks (e.g. "three near-deaths fighting alone"), since only the gradual variant currently exists in code.

## Out of Scope
- Re-touching the dead ActionStyle sub-branches already removed by TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES — re-check that ticket's rationale before wiring into the same function, do not duplicate its work.
- Building a new discrete milestone-event accumulation mechanism if the gradual-only variant is chosen.

## Acceptance Criteria
- [ ] Ticket explicitly corrects the atlas's "no scaffolding" premise and scopes as WIRING HabitBiasService, not building new accumulation state.
- [ ] HabitBiasService.apply_habit_bias gains at least one real production consumer at the ActionStyle bias point, closing the current zero-call-site gap.
- [ ] Mechanism is gated behind a FeatureMode flag, default OFF.
- [ ] PersonalityComponent stays frozen/immutable; habit-accumulation state (HabitMemory or its successor) is applied only through the authoritative apply path.
- [ ] Ticket makes an explicit choice between gradual-accumulation-only vs. also supporting discrete milestone-event marks, not left ambiguous.

## Related Tickets
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION
- TCK-20260809-COMBAT-ACTIONSTYLE-WIRING
- TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/cognition.py
- src/domains/emotion/habit_service.py
- src/content_semantics/personality.py
- src/engine/tactical.py
- src/core/enums.py

## Assumptions / Open Questions
- The choice between gradual-accumulation-only and discrete-milestone variants is open and must be made explicit in this ticket.
- Must default OFF via FeatureMode per the Implementation Patterns table.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
