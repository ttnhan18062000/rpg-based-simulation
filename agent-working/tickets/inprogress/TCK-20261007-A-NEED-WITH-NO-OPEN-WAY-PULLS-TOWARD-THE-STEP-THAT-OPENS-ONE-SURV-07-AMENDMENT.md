---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT
phase: open
date: 2026-10-07
tags: []
---

# TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT

## Title
When none of a hungry subject's ways is open to it now (for example, it cannot pay for the inn meal), its escalated pull goes to the step that opens one: forage or harvest where its kind can, earn and then buy, or ask where a social path exists (decision 27, SURV-07 amendment).

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Found in Lane A's SURV-07 trace on urban_political, seed 42. All 5 hunger-goal defeat deaths were walking to the inn without the 5 gold for a meal; 4 of them had 0 gold. SURV-07 (`TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07`) fixed the futile walk: the inn is offered only to a subject that can pay, per subject (AGENCY-03), and the need is reported as unmet. That leaves a poor subject's need as a countdown timer. The economy never feels hunger.

**Decision 27** (rpg-designer under owner delegation, 2026-10-07) amends SURV-07: "The pull is toward meeting the need, not toward one building. When none of the subject's ways is open to it now, the pull goes to the step that opens one: foraging or harvesting where its kind can, earning where it has paid work and then buying, or asking where a social path exists. Only ways SURV-06 declares for its kind count, and only steps the subject can actually take. A present threat still outranks it. Opening a way is attempted, not guaranteed: a subject with no step it can take stays honestly hungry, and that is SURV-06's poverty outcome."

## Scope
1. The FIRST commit is the designer's decision-27 patch (SURV-07 amendment plus memo row 27). It is cut from this branch's base.
2. With the hunger pull escalated and no open way, score the opening steps the subject can actually take: forage or harvest (where its kind can and a node is reachable), paid work toward the meal price followed by buying, and asking where a social path exists. A present threat gates the pull, as in SURV-07.
3. Make "need pressing, no step available" a typed, inspectable state (durable-state rule), never only a reason string.
4. Measure on the 5-seed bar (seeds 42-46, all three corpus worlds, 1500 ticks) against SURV-07's landed main. Report starvation, total deaths, alive at t=1000 and t=1100, and the counts of each opening step taken.

## Out of Scope
- Any new acquisition mode: theft, raiding, coercive begging, or looting the living. Each would need its own declared Rule.
- Engine charity.
- Changing SURV-06's world-integrity check, which stays per kind and must never become "every subject can afford it".

## Acceptance Criteria
- [ ] Decision-27 patch is the first commit.
- [ ] A subject that cannot pay pursues an available opening step, and a constructed test covers each step kind present in the code.
- [ ] The no-step case is a typed state that shows in the funnel.
- [ ] The 5-seed measurement is reported. Starvation among subjects who cannot pay goes down, and total deaths and the alive counts are not worse beyond 1 SD.

## Related Tickets
- `TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07` (prerequisite)
- `TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD` (the buy path)
- `TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS` (parent epic)

## Related Docs
- `docs/world_rules/life-body/survival-needs.md` (SURV-03, SURV-06, SURV-07); AGENCY-03; memo rows 23, 24 and 27.

## Related Stored Artifacts
- The SURV-07 ticket's probes (`death_trace.py`, `need_funnel.py`) once stored.

## Related Code Areas
- `src/ai/goals/scorers.py`, `src/engine/need_pull.py`, `src/engine/town_resolution.py`, harvest and work scorers.

## Assumptions / Open Questions
- Engineering decisions: how far ahead "in time" allows for a multi-step way, the order among steps, how earning is scored against the escalated need, and when the subject gives up.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
