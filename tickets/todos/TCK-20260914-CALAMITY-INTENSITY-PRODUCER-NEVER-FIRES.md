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
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
