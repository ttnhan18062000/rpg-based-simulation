---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION

## Title
`LegalityServiceV2.verify_attack_legality()` returned FALSE in 100% of a real 330-sample probe
(`urban_political`, 500 ticks) for entities actively pursuing the nearest hostile — split exactly
into `FRIENDLY_FIRE_ILLEGAL` (150, 45%) and `INSUFFICIENT_READINESS` (180, 55%) — the real root
cause of why real combat almost never resolves into damage/kills, deeper than any reward-magnitude
or goal-competition issue

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while investigating `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`'s own real
combat-frequency root cause (per explicit user direction to keep tracing rather than stop at
"raise the reward multiplier"). That investigation ruled out, with real data, 3 successive
hypotheses before reaching this one:

1. **Not hostile scarcity**: a real probe found hostiles within `radius=10.0` in 100% of sampled
   ticks (50/50) for the original population.
2. **Not goal-competition failure**: `CombatEngageScorer`'s own `GoalKind.COMBAT_ENGAGE` wins the
   goal competition in 325/330 samples (98.5%) when available at all — entities are actively
   trying to engage, not choosing other goals instead.
3. **Not a dead code path**: `tactical.py`'s own "ATTACK" branch (when `is_attack_legal`) emits a
   real `TaskUpdate(action="ATTACK", ...)`, routed by `ActionRouter` to
   `CombatActions.execute_attack()`, which genuinely calls
   `CombatResolutionSystem.resolve_attack(entity, target, context)` with a real, non-None
   `context` (`sliding_state`) at the real pipeline call site
   (`src/engine/pipeline_phases/actions.py:165`) — the wiring is intact.

**The real, decisive finding**: `is_attack_legal` (`tactical.py:397`, computed via
`LegalityServiceV2.verify_attack_legality(entity, h, state)` for each candidate hostile,
`tactical.py:392`) was **FALSE for every single one of 330 real samples** in a direct,
instrumented probe. Because it's always false, `tactical.py`'s own decision tree always falls
through to the "else: Pursuit" branch (line 663+) — entities perpetually chase hostiles via
`MovementMode.PURSUE`, never emitting a real ATTACK action, and (since PURSUE is the opposite of
the egress/retreat movement that triggers the corpus's other real kill mechanism,
opportunity-attack) never landing a hit through that path either. **This is the actual root cause
of the corpus-wide low kill rate this whole session's own growth/progression investigation has
been building on** (`TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`,
`TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`) — those tickets treated "real kill rate is
low" as a given fact to design around; this ticket traces *why* it's low.

The 330 real illegal verdicts split cleanly into 2 distinct reason codes, each its own real,
separate investigation thread:

- **`ReasonCode.FRIENDLY_FIRE_ILLEGAL` (150, 45%)**: the legality service's own hostility
  determination disagrees with the simple `entity.identity.faction != target.identity.faction`
  check this investigation's own probe used to select "nearest hostile" — meaning many
  faction-mismatched entities are NOT actually considered legally hostile by the real service.
  Possibly related to the same faction/role-tagging inconsistencies this session already found
  corpus-wide (`TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`'s own "monster mistagged
  as CITIZEN" finding, and the deferred `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`) —
  not confirmed, a real lead to check.
- **`ReasonCode.INSUFFICIENT_READINESS` (180, 55%)**: entities frequently lack enough combat
  readiness to attack. `execute_attack()`'s own attacker update costs `readiness_delta=-100.0` per
  real attack (`combat_actions.py:64`) — whether readiness regenerates fast enough relative to
  this cost, or whether some other mechanic keeps readiness perpetually low, is not yet traced.

## Scope
1. **Investigate** (mandatory before Plan):
   - Trace `FactionSemanticsService`/`RelationContext`'s own real hostility determination for the
     specific faction pairs seen in the 150 `FRIENDLY_FIRE_ILLEGAL` samples — confirm whether
     these are genuinely non-hostile per real faction-tension config (a content/design question)
     or a real bug in the hostility-check logic itself (e.g. reading the wrong faction, or a
     stale/incorrect faction field — cross-reference the deferred role-mistagging investigation).
   - Trace `LegalityServiceV2.verify_readiness()`/whatever computes real readiness regen rate —
     confirm the real numeric regen-per-tick vs. the 100-point cost per attack, and whether
     readiness is being drained by something else concurrently (movement, other actions).
   - Reproduce on a second world to confirm this isn't `urban_political`-specific.
2. **Plan**: once both real causes are separately confirmed, decide whether they need 1 fix or 2
   (they may have entirely independent real causes and fixes — do not assume a shared cause without
   checking, matching this session's own established discipline after the `TCK-20260808-LEVEL-UP-
   GATED-PROGRESSION-CASCADE-DEAD` ticket's own correction).
3. **Implement**: the real, minimal, evidence-grounded fix(es), re-verified via the same real
   `is_attack_legal` instrumented probe this investigation used (target: a real, non-zero legal
   rate, not necessarily 100%).

## Out of Scope
- `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`'s own original XP-multiplier work
  (reverted, not part of this ticket) — this ticket addresses the deeper, real cause that
  ticket's own investigation surfaced.
- Flee/escape/personality-driven combat-outcome diversity — filed separately as
  `TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY` (a real, distinct feature idea, not part
  of this bug investigation).

## Acceptance Criteria
- [ ] investigation.md traces the real cause of `FRIENDLY_FIRE_ILLEGAL` (content/config gap vs.
      real code bug)
- [ ] investigation.md traces the real cause of `INSUFFICIENT_READINESS` (regen rate vs. cost
      imbalance, or a different real cause)
- [ ] Real fix(es) land, re-verified via a real instrumented `is_attack_legal` probe showing a
      non-zero legal rate
- [ ] Downstream re-verification: real `resolve_attack()`/`entity_killed` volume increases in a
      real corpus run, cited honestly (not assumed)
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD (the ticket whose own Investigate phase
  found this — XP-multiplier work reverted there, real fix belongs here instead)
- TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX (DONE — established the real low-kill-rate
  symptom this ticket explains the mechanism for)
- TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION (deferred — possible shared cause with
  `FRIENDLY_FIRE_ILLEGAL`, cross-reference during Investigate)
- TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY (sibling — a distinct feature idea filed
  alongside this bug investigation)

## Related Docs
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` (the foundation audit this whole
  investigation chain traces back to)
- `docs/mechanics/02_combat_laws.md` (real combat legality rules, if documented)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD/` (the real probe data
  and trace this ticket is grounded in)

## Related Code Areas
- `src/engine/legality.py` (`LegalityServiceV2.verify_attack_legality`, `verify_readiness`)
- `src/content_semantics/faction.py`, `src/content_semantics/relation.py` (hostility determination)
- `src/engine/tactical.py` (lines ~387-397, the real `is_attack_legal` computation site)

## Assumptions / Open Questions
- Whether `FRIENDLY_FIRE_ILLEGAL` and `INSUFFICIENT_READINESS` share a root cause — not assumed.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
