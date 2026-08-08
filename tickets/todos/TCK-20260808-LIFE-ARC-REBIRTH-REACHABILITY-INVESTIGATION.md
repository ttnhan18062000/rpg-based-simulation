---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION
phase: open
date: 2026-08-08
tags: [progression, simulation-quality]
---

# TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION

## Title
Hero's Journey rebirth (generation ≥2) was never observed in any of 6 real corpus worlds at 2000
ticks — is it realistically reachable content, or effectively dead?

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Child ticket of `TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC`. That epic's own real 2000-tick,
6-world observation data (`docs/simulation_quality/long_run_observations/*.json`, seed 42) shows
`run_metadata.life_arc_detector_reachable: null` in **every one of the 6 worlds** —
`entity_lifecycle_score.py`'s own honest signal that no entity anywhere reached Hero's Journey
generation ≥2 (a rebirth having occurred) within the observed window. This matches
`TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION`'s own earlier, narrower finding (also `null` on
its own real runs) — now confirmed at real 2000-tick length across a 6-world, archetype-diverse
sample, not just one prior run.

`life_arc_incoherent` (`docs/simulation_quality/quality_scoring_contract.md` §7.6) can only ever
fire once a rebirth has already happened (it checks whether a generation-2+ entity is still level
1 with zero skills) — if rebirth itself is unreachable under real play, this entire scoring rule
is permanently dormant corpus-wide, not because nothing is wrong, but because its own precondition
never occurs.

## Scope
1. **Investigate** (mandatory before Plan):
   - Find the real rebirth/generation-advancement trigger path in `src/` (likely
     `src/engine/combat.py`'s `classification.rebirth_eligible`/`generation_delta` logic, seen
     during this session's own `PROGRESSION-GROWTH-ECONOMY` investigation at
     `combat.py:182-188`: `if classification.rebirth_eligible: if defender.lifecycle.generation <
     4: gen_delta = 1...`). Confirm the real, full precondition chain for a rebirth to occur.
   - Determine whether rebirth requires a HERO to be defeated under `rebirth_eligible`
     circumstances specifically (i.e. is this about HEROES dying and being reborn, not monsters?)
     — if so, cross-reference this session's own `TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF`
     finding that HERO entities are relatively rare (n=24 corpus-wide in the earlier full-corpus
     run) and mostly non-routing — a real, compounding reachability factor.
   - Check whether `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`'s own findings (kill
     rate, XP rate) bear on this — if entities rarely reach meaningful levels/skills at all, a
     rebirth precondition tied to level/skill state could compound with that ticket's own root
     cause. Coordinate rather than duplicate if so.
   - Estimate the real tick/kill-count budget rebirth would realistically require given the real
     measured rates, and compare against this session's own established long-run tier (2000-5000
     ticks) — is rebirth reachable at ANY practical tick length, or does it require orders of
     magnitude longer?
2. **Plan**: based on Investigate's own real findings, decide: is this working-as-intended (rare
   by design, matching the `wilderness_survival` archetype-correct precedent — some content is
   legitimately meant to be rare), or a real reachability gap worth addressing (and if so, at what
   layer: threshold, rate, or trigger-path)?
3. **Implement**: only if Investigate concludes a real gap exists — do not force a fix to make
   `life_arc_detector_reachable` flip to `true` if the honest conclusion is "rare by design."

## Out of Scope
- `life_arc_incoherent`'s own scoring formula/weight — this ticket is about whether its
  precondition (rebirth) is reachable at all, not the formula's own correctness once reachable.
- Re-designing the Hero's Journey/rebirth mechanic wholesale — any change, if warranted, should be
  the smallest one Investigate's own real root cause supports.

## Acceptance Criteria
- [ ] investigation.md traces the real, full rebirth-trigger precondition chain in `src/`
- [ ] investigation.md reports a real estimate of practical reachability (tick/kill-count budget
      required) given real measured rates, not a guess
- [ ] investigation.md reaches an evidenced conclusion: working-as-intended vs. real gap
- [ ] If a real gap is found and fixed: re-verified via the real long-run observation tier showing
      `life_arc_detector_reachable: true` on at least 1 world
- [ ] If working-as-intended: documented as such (matching the archetype-correct precedent), not
      silently closed with no artifact
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC (parent epic)
- TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION (DONE — the earlier, narrower `null` finding
  this ticket confirms and investigates at real scale)
- TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX (sibling child — possible shared root
  cause in real growth rate)
- TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF (DONE — HERO-entity rarity/routing finding,
  possibly compounding)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §7.6 (`life_arc_incoherent`)
- `docs/mechanics/01_entity_anatomy.md` (Hero's Journey / generation mechanics, if documented
  there)
- `docs/simulation_quality/long_run_observations/*.json` (the real data confirming `null`
  corpus-wide)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION/`

## Related Code Areas
- `src/engine/combat.py` (`classification.rebirth_eligible`, `generation_delta`)
- `src/engine/combat_rewards.py` (`CombatRewardClassificationService`)
- `src/simulation_quality/scorers/progression.py` (`life_arc_incoherent`)

## Assumptions / Open Questions
- Whether rebirth is HERO-specific or applies to any entity kind — not assumed; Investigate must
  trace the real code path.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
