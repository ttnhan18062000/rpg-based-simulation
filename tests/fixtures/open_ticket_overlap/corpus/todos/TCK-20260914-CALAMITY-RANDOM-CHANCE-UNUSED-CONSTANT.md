---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT
phase: open
date: 2026-09-14
tags: [world]
---

# TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT

## Title
`CalamityService.CALAMITY_RANDOM_CHANCE = 0.005` is declared but has zero real usages anywhere — a
random-chance-shaped constant sitting inert beside the real, fully-deterministic spawn gate it looks
like it should influence

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found while investigating `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s Finding 4/5
(the `CalamityService.process_world_dynamics()` maturity-independent `world_boss` spawn path).
`CalamityService.CALAMITY_RANDOM_CHANCE = 0.005` (`src/world/calamity.py`) is declared as a class
constant but — confirmed via exhaustive grep of `src/` — has **zero real usages** anywhere outside
its own declaration line. The actual `should_spawn` gate next to it is driven entirely by a
deterministic interval check (`state.tick - state.last_calamity_tick >= CALAMITY_MIN_INTERVAL` AND
`state.tick % CALAMITY_FORCE_INTERVAL == 0`), not any random roll, despite this constant's name and
value strongly suggesting it was meant to gate something probabilistically.

This is the same silence-as-failure-mode family flagged repeatedly this week, but in its most inert
form: it doesn't silently produce a wrong result (nothing reads it), it's just dead weight that
misleads a reader into thinking calamity spawning has a random-chance component it does not have.

## Scope
- Determine why `CALAMITY_RANDOM_CHANCE` exists unused — check git blame / any related doc or
  ticket for whether it was ever wired and later orphaned, or declared and never connected.
- Decide and implement one of: (a) wire it into `should_spawn` as originally likely intended (real
  design decision, may need peer/user sign-off since it changes spawn behavior), or (b) delete it
  as dead code if no real intent can be found and the deterministic-only gate is confirmed correct
  as-is.
- Small, single-file change either way.

## Out of Scope
- The maturity/trauma gate reachability question itself — tracked in the sibling ticket
  (`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`), not this one.
- Any other calamity-system behavior change beyond this one constant.

## Acceptance Criteria
- [ ] Either `CALAMITY_RANDOM_CHANCE` is wired into real spawn logic with a stated rationale, or
      removed as confirmed dead code.
- [ ] No change to `should_spawn`'s existing deterministic interval behavior unless that's the
      explicit intent of the fix (option a).
- [ ] Grep-confirmed no other unused reference is left behind.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (the investigation that surfaced this)

## Related Docs
- None yet.

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/world/calamity.py` (`CalamityService.CALAMITY_RANDOM_CHANCE`, `should_spawn` logic in
  `process_world_dynamics()`)

## Assumptions / Open Questions
- Whether this constant was ever wired and later orphaned during a refactor, or declared and never
  connected in the first place, is not yet known — first investigation step for whoever picks this
  up.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
