---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE

## Title
Real hostile pairs, now correctly detected after
`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`'s identity-resolver fix, never converge to
melee range (`combat.range=1`) within a 2000-tick corpus run — every legality check observed so
far fails on `ReasonCode.OUT_OF_RANGE`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct follow-up to `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (DONE, same session), which
fixed a real bug silently collapsing most of the corpus's real, content-driven faction identities
to `"neutral"` for hostility-detection purposes. After that fix, real hostile pairs
(`goblin_warband`↔`undead_remnants`, `bandit_company`↔`wild_beast_pack`/`merchant_league`) are
now genuinely detected and attempt real attack-legality checks — 26+ real checks observed in a
2000-tick `dungeon_crawl` run, versus 0 before the fix. **Every single one of them still fails**,
100%, with `ReasonCode.OUT_OF_RANGE` — sampled real distances at check-time: 2, 5, 7, 10, 12
against an attacker `combat.range` of `1` (melee/adjacency-only). `readiness=100.0` in every
sampled case (not readiness-blocked). Real `combat_damage`/`entity_killed` events remain zero in
the same 2000-tick window.

Per `tactical.py`'s own documented decision tree (`docs/audits/D21_entity_lifecycle_foundation_
layers.md`'s "Combat legality always false" section), a legality-check failure falls through to
the `else: Pursuit` branch (`MovementMode.PURSUE`), which should close the distance over
subsequent ticks. This ticket investigates why that pursuit does not appear to succeed within a
real 2000-tick window for these real, now-correctly-detected hostile pairs.

## Scope
1. **Investigate** whether pursuit is genuinely attempted for these specific entities (confirm
   `MovementMode.PURSUE` is actually set, not silently overridden by kiting/retreat/other
   higher-priority branches in `tactical.py`'s own decision tree — several of which run *before*
   the legality check on every call, per `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`'s own
   investigation trail through the same function).
2. Trace whether the sampled distances (2, 5, 7, 10, 12) represent a single pursuit arc that
   never converges (oscillating or stalling) or multiple independent, never-followed-up
   encounters (anti-stalemate `STALEMATE_BREAK`/leash `LEASH_RETURN` resetting the chase before
   it converges) — real, live-instrumented evidence, not assumed.
3. Determine whether this is a movement-speed/pacing issue (targets moving away faster than the
   pursuer closes), a target-re-selection issue (switching targets before converging on one), or
   a genuine movement-resolution bug.
4. Produce a concrete recommendation and fix if the cause is clearly scoped; otherwise split
   further per the Uncertainty Rule.

## Out of Scope
- `EntityIdentityResolver`'s own fix (already shipped, `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`) — not revisited.
- Building a ranged-attack mechanic or changing `combat.range` values — this ticket investigates
  why pursuit doesn't close existing melee range, not whether melee range itself is the right
  design.
- Per-attack tactical-modifier trace, pillar-scoring decisions — separate threads.

## Acceptance Criteria
- [ ] investigation.md identifies, with real live-instrumented evidence, the specific reason
      pursuit does not converge hostile pairs to melee range within a 2000-tick window
- [ ] A concrete recommendation is produced (fix vs. further split), with reasoning
- [ ] If a fix lands: real corpus re-verification shows at least one real, non-zero
      `combat_damage`/`entity_killed` event in a 2000-tick run of `dungeon_crawl` or
      `urban_political`

## Related Tickets
- TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE (DONE, same session — the identity-resolver fix
  that surfaced this finding)
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION,
  TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (DONE, same session — readiness/
  friendly-fire fixes; confirmed not the cause here, readiness is 100.0 in every sampled case)

## Related Docs
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` ("Combat legality always false" section,
  2026-08-09 update)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE/investigation.md` (the real
  probe methodology and sample data this ticket continues from)

## Related Code Areas
- `src/engine/tactical.py` (`evaluate_entity_intent`'s `else: Pursuit` fallback and every
  higher-priority branch that runs before it)
- `src/engine/movement.py` (`MovementSystem.resolve_move`, `MovementMode.PURSUE` resolution)
- `src/engine/rpg_depth.py` (`LeashService.is_beyond_leash`/`should_give_up_chase`)

## Assumptions / Open Questions
- Whether 2000 ticks is simply not enough real simulated time for pursuit to converge at the
  corpus's own real movement speeds, vs. a genuine bug — left open per the Uncertainty Rule.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
