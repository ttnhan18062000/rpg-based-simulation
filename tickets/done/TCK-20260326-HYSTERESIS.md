---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260326-HYSTERESIS
phase: done
date: 2026-03-26
tags: [hysteresis]
---

# TCK-20260326-HYSTERESIS

## Title
Goal Hysteresis & Anti-Oscillation System

## Priority
P1

## Description
Entities oscillate between states (Combat↔Flee, Loot↔Wander) when their scores are near decision boundaries. The existing `HysteresisModifier` (1.25x boost to current goal) is insufficient — a mere 25% bonus is easily overcome by large score swings (e.g., HP crossing the flee threshold causes +200% flee score). This sub-ticket implements robust anti-oscillation with minimum commitment duration and cooldown penalties.

## Scope
- **Minimum Commitment**: Entities must commit to a goal for N ticks before re-evaluation.
- **Cooldown Penalty**: Recently abandoned goals receive a score penalty to prevent flip-flopping.
- **Threshold Deadbands**: Apply generous thresholds (e.g., flee at 30%, but don't stop fleeing until 50%).
- **Enhanced HysteresisModifier**: Scale the boost based on how long the entity has held the goal.

## Acceptance Criteria
- [ ] Entities hold a goal for at least `min_commitment_ticks` before switching.
- [ ] Recently abandoned goals receive a cooldown penalty for `cooldown_ticks`.
- [ ] Flee/Combat boundary uses deadband logic (different enter/exit thresholds).
- [ ] No new test regressions (704/704 must still pass).
- [ ] TDD: All behavioral transitions covered by new tests.

## Related Tickets
- TCK-20260322-RPG_REFINEMENT (Parent)

**Tier:** standard
**Type:** chore
**Priority:** P1
