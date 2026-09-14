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
BLOCKED

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
**Ordering conclusion, recorded here so a future reader cannot open the gate without hitting the
prerequisite: the maturity/trauma gate is not the first thing to fix here — it's the last.** A
real, previously-undiscovered defect was found waiting behind it (`difficulty_tier=5` silently
produces tier-1 stats for both world bosses and Lair occupants — see investigation.md's own Defect
1), and opening the gate before fixing that defect would make a rare, hard-won encounter into a
trivial one-shot kill — actively worse than the mechanism staying dormant. **Real sequencing: fix
the tier-5 stat defect first, verify a spawned boss/occupant is actually formidable, and only then
make the gate itself reachable.**

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
**2026-09-14: investigation complete, no code changed — both peer-flagged gaps are now closed,
bringing the full picture back for the fix decision. Ticket stays BLOCKED pending that decision,
not yet ready to close.** Full detail in staging_artifacts/investigation.md. Summary:
- **Ordering conclusion**: fix the tier-5 stat defect first, verify formidability, only then open
  the gate — opening the gate first would ship a broken, anticlimactic encounter.
- **Defect 1**: `difficulty_tier=5` (used by both world-boss and Lair-occupant spawning) silently
  falls back to tier-1 stats — `DIFFICULTY_TIERS` only defines tiers 1-4. Verified empirically: a
  "world boss" spawns with `hp=50/atk=10/level=3`, weaker than an ordinary tier-4 monster
  (`hp=200/atk=30/level=11`). Named explicitly as the 4th instance this week of the same
  silence-as-failure-mode family (dead `spatial_grid` optimization, a bare-except lead-parse
  swallow, a trace recorder logging SUCCESS for a no-op).
- **Defect 2 (now chased to a definitive answer)**: the world boss's own signature loot
  (`item_id="ancient_core"`) does NOT crash — it is silently dropped during inventory add
  (`src/core/inventory.py::apply_update()`'s `if not defn: continue`, via the real, non-raising
  `src.core.items.ItemRegistry` that the actual inventory/equipment pipeline uses, not the
  raising `src.core.registries.ItemRegistry` initially assumed). A real second defect (a fixed,
  formidable world boss would still drop nothing today), but not a build prerequisite for Defect 1.
- **Defect 3**: both halves of the gate's own AND conjunction are independently unreached in a
  real 2000-tick run — `state.maturity` reached `1` (need `≥50`), `trauma_score` peaked at `9.92`
  (need `≥20.0`). Not "one large number."
- **Finding 4/5 (now measured)**: a second, maturity-independent `world_boss` spawn path exists
  (`CalamityService`), correctly tiered, gated on `tick % 5000 == 0` AND some region's
  `calamity_intensity > 0.3`. A real, instrumented 5000-tick simulation (`frontier_living_world`,
  seed=42) found `calamity_intensity` never left `0.0` in any region for the entire run — this
  path is itself unreached in practice, independent of the maturity/trauma gate, and never spawns
  Lair occupants regardless. Also found (filed as two small follow-up tickets, not fixed here): an
  unused `CALAMITY_RANDOM_CHANCE` constant, and a real drift between two parallel `_BOSS_KINDS`
  observability constants.

## Test Summary
_(none — investigation only; findings verified via direct probes against constructed real states,
not committed as test files, since no fix has been chosen yet)_

## Files Changed
_(none — investigation only, per this ticket's own explicit instruction)_

## Completion Summary
_(not complete — investigation ongoing per peer's own explicit "keep investigating, don't build
yet" instruction; staging_artifacts/investigation.md has the full picture gathered so far)_
