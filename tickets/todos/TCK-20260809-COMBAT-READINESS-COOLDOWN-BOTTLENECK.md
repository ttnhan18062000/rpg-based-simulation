---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK

## Title
Investigate whether the real post-attack readiness cooldown (a full -100.0 reset, regenerating
at `readiness_speed=10.0/tick`, i.e. 10 ticks to recover) is now the dominant bottleneck
suppressing sustained combat, now that identity-resolution and pursuit-tracking are fixed

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct continuation of the user's own combat-investigation request. With
`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (identity resolution) and
`TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE` (live target tracking) both fixed, real hostile
pairs are now detected and pursuit genuinely converges (real `is_attack_legal` rate improved
from 0% to 44% in `dungeon_crawl`). The next real candidate bottleneck, per
`docs/mechanics/02_combat_laws.md` §7's own documented law: every successful attack resets the
attacker's `readiness` by a full `-100.0`, and passive regeneration is `readiness_speed`
(default `10.0/tick`) — meaning an attacker is legally ineligible to attack again for a real,
minimum 10 ticks after every single attack, regardless of target proximity or continued
hostility.

Combined with `TacticalDecisionSystem.evaluate_entity_intent()`'s own real ~10-tick brain-cadence
gate (`SystemCadence.strategic_intelligence`, confirmed load-bearing by the sibling pursuit-
tracking ticket), this creates a real, plausible compounding effect: an entity that successfully
lands one attack becomes both readiness-blocked AND brain-cadence-blocked for roughly the same
~10-tick window, meaning sustained multi-hit combat sequences (the kind that would actually
produce a kill against anything but the lowest-HP targets) may be structurally rare — not because
hostiles can't be found or reached, but because the attacker can't act again fast enough to
finish what it started before its own target (or the tactical situation) has moved on.

## Scope
1. **Investigate**: live-instrumented, real corpus trace of the actual real gap between
   consecutive `ATTACK` attempts by the same attacker against the same (still-alive) target —
   confirm whether readiness or brain-cadence is the actual binding constraint in practice (they
   may not both apply simultaneously — e.g. if `STUCK-ATTACK-TASK-DEAD-TARGET`'s own fix changes
   how quickly a live attacker re-engages). Check real corpus data for how many real combat
   sequences involve more than one hit from the same attacker vs. a single hit followed by
   disengagement/target-loss.
2. **Determine** whether this is a real design intent (readiness as a deliberate pacing
   mechanism, matching its own documented "cooldown gate" framing) vs. an unintentionally severe
   compounding effect with the brain-cadence gate that undermines sustained combat specifically.
3. **Produce a concrete recommendation** (tune `readiness_speed`, decouple/desynchronize the two
   cadences, or document as intentional pacing) — per the Uncertainty Rule, do not force a fix
   before the evidence narrows the real cause.

## Out of Scope
- Any change to `calculate_damage()`/`resolve_attack()`'s own resolution logic.
- Rebalancing `readiness_speed`'s default value without real, corpus-verified evidence that a
  specific new value measurably improves sustained combat without new side effects.
- `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET`'s own bug — a related but distinct finding
  (a stuck task retried with no cooldown gate at all, vs. this ticket's own question of whether
  the *intended* cooldown is itself too long relative to real combat pacing needs).

## Acceptance Criteria
- [ ] investigation.md presents real, live-instrumented evidence of the actual real gap between
      consecutive attacks by the same attacker, and which constraint (readiness, brain-cadence,
      target loss, or some combination) is empirically binding
- [ ] A concrete recommendation is produced (fix vs. document as intentional), with reasoning
- [ ] If a fix lands: real corpus re-verification shows a measurable increase in multi-hit combat
      sequences or kill rate

## Related Tickets
- TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET (same session — a related but distinct
  finding about a *different* combat-pacing failure mode)
- TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE, TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION,
  TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (DONE, same session — the real
  readiness-mechanics history this ticket builds on)

## Related Docs
- `docs/mechanics/02_combat_laws.md` §7 (Action Legality & the Readiness Gate — the real,
  documented cooldown law this ticket investigates)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/legality.py` (`verify_attack_legality`'s readiness check)
- `src/core/state.py` (`CombatComponent.readiness_speed`)
- `src/engine/cadence.py` (`SystemCadence.strategic_intelligence`)
- `src/engine/domain/cognition.py` (`CognitionDomain.execute_brain`'s cadence gate)

## Assumptions / Open Questions
- Whether readiness cooldown is a deliberate design choice (pacing combat to feel less like
  spam-clicking) that should be left alone, vs. an unintended severity — left open per the
  Uncertainty Rule.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
