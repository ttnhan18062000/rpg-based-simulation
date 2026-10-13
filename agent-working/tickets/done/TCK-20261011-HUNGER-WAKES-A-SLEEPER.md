---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261011-HUNGER-WAKES-A-SLEEPER
phase: done
date: 2026-10-11
tags: []
---

# TCK-20261011-HUNGER-WAKES-A-SLEEPER

## Title
Hunger wakes a sleeper: a held SLEEP or REST ran no brain, so a starving subject slept through its own starvation.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Never-ate pattern 1 (scout #17 and merchant #19 slept from hunger about 96 to death, 300 to 400 ticks), ruled by the owner 2026-10-11 as a SURV-07 x decision 41 amendment (rpg-planner dispatch).

## Scope
The need wake (#505) extends from a held ENTITY_MOVE to a held SLEEP or REST: hunger at ESCALATION_ONSET wakes the brain on the strategic cadence; a collapse holds until the debt is below the collapse line.

## Out of Scope
Sleep-debt wake of a sleeper (debt is high by nature); the earn path; a bed charge on re-decision.

## Acceptance Criteria
A chosen sleep woken by hunger; a collapse held then woken; no wake-collapse loop over 100 ticks; a sated sleeper not woken.

## Related Tickets
TCK-20261009-HEROES-ON-A-LEASH-NEVER-SEEK-FOOD-AND-STARVE-WITHOUT-ONE-EAT-ATTEMPT; TCK-20261011-A-PANIC-RETREAT-TO-ITS-OWN-TILE-IS-HELD-WITH-NO-THREAT-IN-SIGHT

## Related Docs
docs/mechanics/04_strategic_cognition.md; docs/guidelines/intentional_divergences.md Section 2.115; docs/parity_ledger/strategic_cognition.yaml STRAT-283.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/scheduler.py, src/engine/need_pull.py.

## Assumptions / Open Questions
The owner's rejected options are in the designer memo (not restated).

## Implementation Notes
Measured vs rpg-fold-next fe1270233, seeds 42 to 46, 5000 ticks: never-ate urban 0 to 0, frontier 1.2 to 1.0; hungry-asleep ticks urban -443 (SE 398), frontier -1115 (SE 718); deaths within noise. Traced #19 is fed in both arms after the panic fix, so the effect here is within noise (disclosed).

## Test Summary
tests/unit/engine/test_hunger_wakes_a_sleeper.py (7) and the earlier need-wake tests pass.

## Files Changed
src/engine/scheduler.py, src/engine/need_pull.py, tests, docs.

## Completion Summary
Hunger wakes a sleeper; divergence 2.115, STRAT-283.
