---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260627-P3A-DEFERRED-EPICS
phase: done
date: 2026-06-27
tags: [p3, deferred, epic-tracking, post-stabilization, long-run]
---

# TCK-20260627-P3A-DEFERRED-EPICS

## Title
Tracking: Deferred P3 feature epics (post P0–P2 stabilization)

## Status
DONE

## Tier
epic

## Type
chore

## Priority
P3

## Request Summary
7 partially-implemented or unvalidated features are deferred until P0–P2 are resolved. Each may spawn its own epic when conditions are met. This ticket tracks the gate conditions and feature areas. Source: D01 [P] items.

## Scope
Track and gate the following deferred epics:

| Sub-item | Gate Condition | Gate Status (2026-06-28) | Child Epic |
|---|---|---|---|
| Resource Ecology Regeneration | P0 fixes complete; run D06 5,000-tick | PARTIAL — P0 done; 5k-tick run pending | TCK-20260628-E-RESOURCE-ECOLOGY (BLOCKED) |
| World Evolution System | P0 fixes + D06 5,000-tick run | PARTIAL — P0 done; 5k-tick run pending | TCK-20260628-E-WORLD-EVOLUTION (BLOCKED) |
| Narrative Consequence Layer | E51/E43B episode-boundary systems complete | MET ✓ — E51 and E43 both DONE | TCK-20260628-E-NARRATIVE-CONSEQUENCE (OPEN) |
| Full Party Adventure Loop | E61B implemented + HERO role populated | PARTIAL — E61B done; HERO role unclear | TCK-20260628-E-PARTY-LOOP (BLOCKED) |
| Personality → Long-Run Behavior Calibration | P0-A fix; run D05-style audit at 1,000+ ticks | PARTIAL — P0-A done; audit run pending | TCK-20260628-E-PERSONALITY-CALIBRATION (BLOCKED) |
| Combat Ecology Extension | D06 5,000-tick data available | NOT MET — 5k-tick run pending | No epic yet |
| Long-Horizon Regression Suite | P1-A rejection cascade fix | MET ✓ — P1-A DONE | TCK-20260628-E-LONGRUN-REGRESSION (OPEN) |

## Out of Scope
- Implementation of any deferred item in this ticket — each gets its own epic when the gate condition is met.

## Acceptance Criteria
- [x] This tracking epic is updated when gate conditions are met for each sub-item.
- [x] When a gate condition is satisfied, a new child epic ticket is created and linked here.
- [x] Long-Horizon Regression Suite epic is created immediately after P1-A is complete (highest-value first unblock).

## Related Tickets
- TCK-20260627-P1A-REJECTION-BACKOFF (gates Long-Horizon Regression Suite — DONE)
- TCK-20260627-P0A-ADVENTURE-FLAG (gates Resource Ecology, World Evolution, Personality Calibration — DONE)
- TCK-20260628-E-LONGRUN-REGRESSION (child epic — gate MET, OPEN)
- TCK-20260628-E-NARRATIVE-CONSEQUENCE (child epic — gate MET, OPEN)
- TCK-20260628-E-RESOURCE-ECOLOGY (child epic — gate partial, BLOCKED on 5k-tick run)
- TCK-20260628-E-WORLD-EVOLUTION (child epic — gate partial, BLOCKED on 5k-tick run)
- TCK-20260628-E-PARTY-LOOP (child epic — gate partial, BLOCKED on HERO role verification)
- TCK-20260628-E-PERSONALITY-CALIBRATION (child epic — gate partial, BLOCKED on D05 audit run)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` §[P] items
- `docs/plans/long_term_development_roadmap.md`

## Related Stored Artifacts
- N/A

## Related Code Areas
- Various — per sub-item above

## Assumptions / Open Questions
- "Long-Horizon Regression Suite" is the most directly unblocked item after P1-A (rejection cascade fix).

## Implementation Notes
- When creating child epics: follow the standard epic tier workflow.
- Update this ticket's Related Tickets section as children are created.
- **2026-06-28:** Gate check run. All P0, P1, P2, and other P3 tickets confirmed DONE.
  Two gates fully met: Long-Horizon Regression Suite (P1-A done) and Narrative Consequence
  Layer (E51/E43 done). Four gates partially met (blocked on 5k-tick run or HERO role).
  One gate not yet met: Combat Ecology Extension (needs 5k-tick data — no epic created yet).
  Six child epics created; see Related Tickets above.

## Test Summary
N/A — tracking ticket.

## Files Changed
- `tickets/todos/TCK-20260628-E-LONGRUN-REGRESSION.md` — new epic (gate MET)
- `tickets/todos/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md` — new epic (gate MET)
- `tickets/todos/TCK-20260628-E-RESOURCE-ECOLOGY.md` — new epic (BLOCKED on 5k-tick)
- `tickets/todos/TCK-20260628-E-WORLD-EVOLUTION.md` — new epic (BLOCKED on 5k-tick)
- `tickets/todos/TCK-20260628-E-PARTY-LOOP.md` — new epic (BLOCKED on HERO role)
- `tickets/todos/TCK-20260628-E-PERSONALITY-CALIBRATION.md` — new epic (BLOCKED on D05 audit)
- `tickets/inprogress/TCK-20260627-P3A-DEFERRED-EPICS.md` — updated scope table, AC, Related Tickets, Implementation Notes

## Completion Summary
Gate-check run on 2026-06-28. All P0, P1, P2, and other P3 tickets confirmed DONE (26 tickets).
Two deferred items are now fully unblocked: Long-Horizon Regression Suite (P1-A done) and
Narrative Consequence Layer (E51/E43 done). Four items are partially unblocked (P0 done but
5k-tick run or calibration audit not yet completed). One item (Combat Ecology Extension) remains
fully gated pending 5k-tick data. Six child epic tickets created in tickets/todos/. No production
code was changed.
