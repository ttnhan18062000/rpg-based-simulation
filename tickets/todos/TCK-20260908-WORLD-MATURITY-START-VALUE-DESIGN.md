---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN
phase: open
date: 2026-09-08
tags: [world, architecture]
---

# TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN

## Title
Decide whether a world should be compilable at a non-zero starting world maturity

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Found during `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE`'s follow-up pass. The Lair-occupant gate
(`state.maturity >= 50.0`, world-level) has no compile-time content-seed path in the schema, and
natural accrual is genuinely slow: `CalamityService.apply()` (`src/world/calamity.py:30-32`)
increments `state.maturity` by 1 on a plain, unconditional periodic schedule
(`state.tick % MATURITY_INTERVAL == 0`, `MATURITY_INTERVAL = 1000` — not tied to whether a calamity
actually fires), so reaching `state.maturity >= 50` needs ~50,000 ticks — far beyond any practical
calibration run (this repo's own runs are 200-5,000 ticks).

Unlike the camp-maturity gate `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` fixed via content
authoring (`CampState.maturity` is a real, per-camp, content-authorable field), `state.maturity` is
a single global counter — there is no per-lair or per-region equivalent. "Seeding" it isn't a
lair-content change at all; it's a global world-age override that would simultaneously
fast-forward every other maturity-gated mechanism in the simulation (not just Lair occupants),
a materially wider blast radius than the schema gap suggests.

## Scope
- Confirm during Investigate whether `world.maturity >= 50` genuinely gates only the Lair-occupant
  spawn, or whether other real mechanisms also key off `state.maturity` at various thresholds
  (re-grep for `state.maturity` comparisons across `src/`) — the real blast radius of any change
  here needs to be understood before deciding.
- Design and decide: should `WorldComposition`/`RegionSpec`'s own schema gain a real
  `starting_world_maturity` (or similar) field, letting a world compile with a non-zero
  `state.maturity` from tick 0? Or is this better left as a disclosed, accepted long-horizon gap
  (matching this epic's own precedent for similarly-gated mechanisms)?
- If a new field is added: confirm it doesn't silently change behavior for every existing world
  that doesn't set it (default must stay 0, current behavior unchanged).

## Out of Scope
- Redesigning `CalamityService`'s own maturity-accrual formula or interval — confirmed correct as a
  design choice, not a bug; this ticket only asks whether a *starting* value should be
  content-authorable.
- The Lair-occupant mechanism itself (`region.trauma_score >= 20.0`, `BossService`) — already
  confirmed correct and tested; this ticket only concerns the world-maturity half of its gate.
- Any other maturity-gated mechanism's own disposition — scope this ticket to the schema/design
  question only, not a survey of every consumer (though Investigate should identify them for real
  blast-radius awareness, per Scope above).

## Acceptance Criteria
- [ ] A real, evidenced decision is made: add a compile-time `starting_world_maturity` field, or
      formally accept the current gate as long-horizon-only with no schema change.
- [ ] If a field is added: default behavior for every existing world is unchanged, and the new field
      is exercised by at least one real corpus/calibration world proving the Lair-occupant gate can
      now fire in a practical run.
- [ ] If accepted as-is: the disposition is recorded in `docs/guidelines/intentional_divergences.md`
      or an equivalent disclosed-gap location, not left as only a ticket-body note.

## Related Tickets
- `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` (`tickets/done/` — found this gap during its own
  follow-up pass)
- `TCK-20260904-LAIR-ENTITY-ANCHOR` (the ticket that originally built the Lair-occupant mechanism)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/world/calamity.py` (`CalamityService.apply()`, `MATURITY_INTERVAL`)
- `src/world/boss.py` (Lair-occupant gate consumer)
- `src/worldbuilding/schema.py`, `src/worldbuilding/compiler.py` (if a new compile-time field is
  added)

## Assumptions / Open Questions
- Whether to add a new schema field or accept the gap as-is is the central real design question
  this ticket must resolve — deliberately not decided here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
