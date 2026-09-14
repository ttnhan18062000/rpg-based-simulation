---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY
phase: open
date: 2026-09-14
tags: [world]
---

# TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY

## Title
`state.maturity >= 50` gates both Lair-occupant spawning and world-boss spawning behind a ~50,000-tick requirement, against a corpus whose runs are 200-5,000 ticks — the user has reversed the prior "accepted long-horizon divergence" disposition and wants this treated as a reachability defect

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`docs/plans/deferred_tuning_decisions_register.md`'s own D-05 entry: `state.maturity` increments
+1 per 1000 ticks (`src/world/calamity.py::MATURITY_INTERVAL`), and both Lair-occupant spawning and
`BossService.check_for_boss_spawn()` (`src/world/boss.py::BOSS_SPAWN_THRESHOLD = 50.0`) require
`state.maturity >= 50` — confirmed via direct read, matching D-05's own claim exactly. That gate
needs ~50,000 ticks to ever open. `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` (done) originally
closed by accepting this as a disclosed long-horizon divergence — a deliberate design choice that
lairs/world bosses are late-game-only content.

**The user has reversed that disposition.** Per D-05's own "wiring-first rule" test ("if this number
stays exactly as it is, does the mechanism still execute in a real run? If no, it is not a deferred
tuning decision — it is a reachability defect"): the honest finding may be that lairs and world
bosses never spawn in any real run at all, which is a feature not delivering, not a number being
intentionally large. The user wants both feature families made reachable.

## Scope
- **Investigation first, no implementation until peer has reviewed what the gate actually needs.**
- Determine whether `state.maturity`'s threshold (`50.0`) or its increment rate
  (`MATURITY_INTERVAL = 1000` ticks) is the wrong half — "the maturity gate is probably a number,"
  per peer's own framing, but confirm rather than assume which number, and what a realistic
  corrected value would be given the corpus's real 200-5,000 tick run lengths.
- Check whether a genuine design intent exists for lairs/world bosses being late-game-only content
  (matching `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN`'s own original closure reasoning) —
  if such an intent is real and documented, that changes what "fixing" this means (a corrected
  number vs. a redesigned trigger entirely).
- **Critically**: check whether Lair-occupant spawning and world-boss spawning actually *work*
  once the maturity gate is past — per this week's own repeated pattern (`combat_engagement`,
  `region_danger_seen`), every other mechanism unlocked this arc had real defects waiting behind
  its own gate. Do not assume the mechanism is otherwise sound just because the gate is the
  disclosed blocker; construct or drive a real state past `state.maturity >= 50` and verify the
  spawn logic actually produces the intended, correct result (a real lair occupant / a real world
  boss with sane parameters), not just that the `if` branch is entered.
- Bring findings (whether it's genuinely a one-value fix, and whether real defects exist behind the
  gate) back for review before any implementation.

## Out of Scope
- Actually changing `BOSS_SPAWN_THRESHOLD`/`MATURITY_INTERVAL`/any spawn logic — investigation
  only, per explicit instruction.
- The faction war declaration reachability question (D-06) — sequenced separately, own ticket
  (`TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION`), different shape of problem.
- Balance/tuning work generally — this ticket is about reachability (does it ever fire), not about
  what the "right" late-game difficulty curve should be.

## Acceptance Criteria
- [ ] A real, evidence-backed answer on whether the maturity threshold or increment rate (or both)
      is the actual blocker, with a concrete corrected value proposed if it's genuinely a one-value
      fix.
- [ ] A real check (not assumption) of whether Lair-occupant/world-boss spawn logic itself is
      correct once the gate is passed — constructed or driven past the gate in a real test/run, not
      just traced statically.
- [ ] Findings brought to peer/user review before any implementation proceeds.
- [ ] No implementation without that review.

## Related Tickets
- `TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN` (done — the ticket that originally accepted
  this as a long-horizon divergence; disposition now being revisited)
- `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` (filed alongside this one, from the same
  user decision — a different reachability/design question, sequenced separately)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` § D-05 (the entry this ticket investigates)
- `docs/world/raid_boss_camp_contract.md` § Boss (spawn conditions)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/world/calamity.py` (`MATURITY_INTERVAL`, the +1-per-1000-ticks maturity increment)
- `src/world/boss.py` (`BossService.check_for_boss_spawn()`, `BOSS_SPAWN_THRESHOLD`)
- Lair-occupant spawning (not yet located precisely — first investigation step: find the real code
  path, matching D-05's own claim that it shares this same `state.maturity >= 50` gate)

## Assumptions / Open Questions
- Whether "50" was ever actually tuned, or whether it's an arbitrary placeholder that was never
  revisited, is the central open question — not assumed either way here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
