---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES
phase: open
date: 2026-09-14
tags: [world]
---

# TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES

## Title
`calamity_intensity` never left `0.0` in any region across a real 5000-tick run — the entire
calamity-intensity system (both its producer and its propagator) appears to be inert in practice,
not just the maturity-independent `world_boss` spawn path that consumes it

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found while investigating `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s Finding 4/5.
A real, instrumented 5000-tick `Kernel.tick_once()` simulation against `frontier_living_world`
(seed=42), tracking `region.calamity_intensity` on every tick for every region, found it **never
moved off `0.0` for the entire run** — not "never crossed the 0.3 spawn-gate threshold," never
changed at all, in any region, at any tick.

`src/world/calamity.py` has two real (non-dead-code) mechanisms for producing/spreading
`calamity_intensity`:
- `CalamityService.apply_calamity_consequences()` — the sole producer: `+0.05` per `entity.kind ==
  "hero"` death specifically inside a `region.hazard_level > 0.5` region, capped at `1.0`.
- `CalamityPressurePropagator.propagate_seasonal()` — spreads *existing* intensity (above
  `PROPAGATION_THRESHOLD = 0.10`) to adjacent regions every `SEASONAL_PROPAGATION_INTERVAL = 500`
  ticks; it cannot create intensity from nothing.

If the sole producer never fires in a real run (no hero died in a `hazard_level > 0.5` region
during the 5000-tick probe — not separately confirmed, but consistent with the observed flat zero),
the propagator has nothing to spread regardless of how many propagation cycles pass. This is the
same silence-as-failure-mode shape found repeatedly this week (a 7th instance): a whole subsystem
that looks wired and tested in isolation, but whose only real trigger condition never occurs in
practice, so the system as a whole is functionally dead without anything erroring or looking broken
in a static read.

This is a separate, deeper finding than the `world_boss` spawn path's own gate
(`calamity_intensity > 0.3` at `tick % 5000 == 0`) — even if that gate's own interval/tick
requirement were made reachable, the intensity value it checks would still never be nonzero.

## Scope
- Confirm directly (not inferred) whether any hero ever died in a `hazard_level > 0.5` region
  during a real run of realistic length — check `region.hazard_level` distributions across the
  corpus's real worlds, and whether hero deaths in high-hazard regions are themselves rare/absent
  for a separate reason (e.g. heroes avoid high-hazard regions by design, or hazard levels are
  themselves miscalibrated/never reach 0.5).
- Determine whether the producer's trigger condition (`hero` kind + `hazard_level > 0.5`) is too
  narrow to ever fire in practice, and if so, propose a realistic wiring fix — a broader trigger
  condition, a lower hazard threshold, or an additional real producer — as a wiring fix, not a
  balance/tuning change.
- Check whether `region.hazard_level` itself is a live, populated stat or another dead/always-zero
  field — if hazard levels themselves never exceed 0.5 anywhere in the corpus, that's the real root
  cause and this ticket's scope should include it.
- Investigation-first is not required to be pre-registered as blocking here (no explicit "no
  implementation until reviewed" instruction was given for this ticket specifically) — but given
  this affects a whole subsystem, bring findings + a proposed fix for review before implementing,
  following this arc's established pattern for reachability defects of this size.

## Out of Scope
- The `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` maturity/trauma gate itself — a
  separate, already-being-fixed reachability defect, not this ticket's concern.
- Balance/tuning of the `0.05`/`0.15`/`0.10`/`0.3` constants themselves, beyond what's needed to
  make the producer fire at all in a realistic run.

## Acceptance Criteria
- [ ] A real, evidence-backed root cause for why `calamity_intensity` never moves in practice —
      either the trigger condition is too narrow, or `hazard_level` itself never crosses the
      required threshold, or both.
- [ ] A proposed wiring fix (not yet built without review) that would make at least one region's
      `calamity_intensity` demonstrably nonzero within a realistic corpus run length.
- [ ] Findings brought to peer/user review before any implementation, matching this week's
      established pattern for reachability-defect tickets of this size.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (the investigation that surfaced this)
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (names the general pattern this ticket is a
  third confirmed instance of: mechanics whose preconditions depend on world geometry/composition
  that nothing validates)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (sibling instance — the dangling-
  region-reference and spatial-isolation findings)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` (candidate for a new entry once root cause is
  confirmed)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/world/calamity.py` (`CalamityService.apply_calamity_consequences()`,
  `CalamityPressurePropagator.propagate_seasonal()`)
- Wherever `region.hazard_level` is set/computed (not yet located — first investigation step)

## Assumptions / Open Questions
- Whether hero deaths in high-hazard regions are rare because of correct emergent behavior (heroes
  successfully avoid dangerous regions) versus a defect (hazard levels miscalibrated, or heroes
  never enter high-hazard regions at all due to an unrelated routing issue) is not yet known.

## Implementation Notes
**2026-09-15, checked directly against the "mechanics whose preconditions depend on world
geometry that nothing validates" pattern named in `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-
ACCUMULATES` — confirmed as a third instance, and a doubly-clean one.**

**First, confirmed `region.hazard_level` itself is a live, real, populated stat** — ruling out
that part of the ticket's own Scope immediately. Grepped every `world_modules/*.yaml`: real,
nonzero hazard levels exist throughout the corpus (`bandit_road`: 2.0, `goblin_camp`: 3.0,
`undead_battlefield`: 4.0, `moon_cave`: 4.0, etc.) — several well above the `> 0.5` threshold this
ticket's own producer checks. Not the root cause.

**Second, checked whether any `entity.kind == "hero"` entities exist at all in
`frontier_living_world`** (the exact world this ticket's own 5000-tick probe used) — compiled it
directly and inspected the real entity roster. **Zero.** `frontier_living_world`'s own module
composition (`frontier_village_core`, `wolf_den_near_forest`, `goblin_camp_conflict`,
`old_mine_resource_loop`, `bandit_road_trade_pressure`, `undead_battlefield`,
`trading_company_hub`) does not include `hero_adventurers` — the only module in this corpus that
produces `kind == "hero"` entities at all. Every other entity kind present
(`worker`/`guard`/`merchant`/`blacksmith`/`scout`/`raider`/`leader`/`predator_hunter`/`sentinel`/
`alpha`) is a non-hero role. **The producer's trigger condition cannot fire in this world for any
value of `hazard_level`, because the required entity kind never exists there at all** — not a
spatial-isolation question at all, an even more basic "the precondition's other half was never
composed into this world" gap.

**Third, checked a world that DOES compose `hero_adventurers`** (`crowded_frontier`) to see
whether the pattern is spatial isolation there instead, matching the lair/merchant instances:
confirmed 3 real `hero`-kind entities exist, but `hero_adventurers.yaml`'s own
`population_recipes` hardcode `spawn_region: "hometown"` for **all three**, unconditionally —
`"hometown"` (`frontier_village_core`'s own region) has `hazard_level: 0.0`. Even in a world where
heroes exist at all, their own module never composes them anywhere near a `hazard_level > 0.5`
region at spawn. Whether AI-driven wandering/questing later moves a hero into a hazardous region
during a real run is a separate, unconfirmed question — but the starting composition never puts
them there, and this session did not trace whether in-run movement closes that gap.

**Conclusion: this is a real, third confirmed instance of the named pattern, and arguably the
cleanest one yet** — two independent, compounding reasons (the entity kind the mechanic needs
often doesn't exist in a world's composition at all; and where it does, its own module hardcodes
it away from every region the mechanic needs it to visit). This gives the pattern three real
instances across three separate mechanics (Lair-occupant spawning, cross-faction combat volume,
calamity-intensity production), each with a distinct specific composition gap but the same shape:
a mechanic's precondition depends on spatial/compositional co-location that nothing in the compile
path validates.

**Parked here, per the same investment cap applied to the sibling tickets in this cluster — not
proposing or building a fix.** Two candidate directions, both design decisions:
1. Compose `hero_adventurers` (or an equivalent hero-kind population) into more worlds, and/or
   change its own `spawn_region` to include (or patrol into) at least one real hazard-bearing
   region, rather than hardcoding all three heroes to `"hometown"`.
2. Broaden the producer's own trigger condition (a different/additional entity kind, a lower
   hazard threshold, or a different triggering event entirely) so it doesn't depend on a specific
   role existing in a specific place — the mechanic-design-level fix, mirroring the lair ticket's
   own second candidate direction.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
**Parked by explicit user decision, not abandoned or unresolved.** The root cause is fully known
and doubly confirmed: the reference world the original probe used has zero `hero`-kind entities
composed into it at all, and even a world that does compose heroes hardcodes their spawn region
to a zero-hazard area. Both facts confirmed by direct inspection of the real compiled entity
roster and the authored content, not inferred. Two real candidate fix directions are recorded
above. The user's explicit decision, given the investment cap on this cluster, was to record the
finding and not build a fix now — "we know exactly why this doesn't fire and chose not to fix it
now" is the accurate state, distinct from "this doesn't fire and we don't know why." See
`docs/plans/world_composition_precondition_gap_finding.md` for the durable record of this finding
alongside its two sibling instances.
