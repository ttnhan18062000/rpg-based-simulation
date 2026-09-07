---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL
phase: open
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL

## Title
Revive the dead Perception → Motivation route-bias pipeline — unlocks idea 57 (Living Legend) and the already-built Culture Drift bias overlay

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Split out of `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (Dormant Mechanism Closure epic, child 1
of 6) on 2026-09-07: that ticket's own Scope assumed idea 57 only needed a new `legend_facts` input
wired into an already-live Perception→Motivation pipeline. Direct investigation found that premise
wrong — this is a foundational, pre-existing gap in the whole route/goal-scoring layer, not specific
to idea 57, and materially larger than a "bridge one signal" fix. Confirmed via direct grep,
2026-09-07:

- **`PerceptionUpdatePhase`** (`src/domains/perception/phase.py`) has **zero real (non-test)
  callers anywhere in `src/`** — the whole phase is never invoked by the live Kernel tick loop, not
  just missing idea 57's signal. `LegendFactService.to_world_signal()` (`src/domains/fame/legend.py`)
  already exists to convert a `LegendFact` into the `WorldSignal` shape this phase expects to
  consume — but there is no live call path that would ever pass it in.
- **`MotivationBiasService.compute_bias_multiplier()`** (`src/domains/motivation/service.py`) also has
  **zero real callers anywhere in `src/`** — the function that would actually turn a perceived signal
  into a route/goal-scoring bias is itself dead. This means the **already-built** Culture Drift bias
  overlay (`CulturalBiasApplicator.compute_culture_delta()`, `src/domains/culture/applicator.py`,
  E62C — whose output `compute_bias_multiplier()`'s own `culture_values` parameter is designed to
  receive) is *also* dormant today, independent of idea 57.

Reviving both subsystems properly unlocks two real, already-shipped mechanisms at once (idea 57's
`LegendFact` route-bias, and the Culture Drift bias overlay), not just one.

## Scope
- Decide where in the live Kernel per-tick pipeline `PerceptionUpdatePhase` should actually run
  (confirm the real, current phase ordering first — don't assume a slot).
- Define the full real `world_signals` set this phase should receive — not just `LegendFact`, since
  no signal source has ever been proven to reach a live entity through this phase; audit what other
  real signal producers exist today (Culture Drift, LegendFact, and any others found during
  Investigate) and decide which belong in v1 of a real wiring vs. a disclosed, deferred follow-up.
- Find or build the real live route/goal-scoring call site that should receive
  `compute_bias_multiplier()`'s output, and wire it through the authoritative apply-path (per this
  repo's own durable-state/architecture rules — decision logic reads state, it does not mutate it
  directly).
- Wire a real Perception/Motivation consumer for `LegendFact` specifically, producing a measurable
  route-bias shift for at least one Townsperson entity, per idea 57's own original design intent
  (`TCK-20260905-FAME-DERIVER-LEGEND-FACT`).
- Add real tests proving the full pipeline (perception → bias computation → route/goal-scoring
  effect) is live-reachable through a real `Kernel.tick_once()` run or real corpus scenario, not just
  proving the pure functions work in isolation (which `PerceptionUpdatePhase`/
  `compute_bias_multiplier()`'s own existing unit tests may already do — confirm and don't duplicate).
- Given the scope (touching the live tick pipeline's phase ordering), this ticket likely warrants an
  `architecture-reviewer` pass on the Plan before Implementation, matching the same caution the
  parent bridge ticket already flagged for touching this layer.

## Out of Scope
- Rebuilding `CulturalBiasApplicator`/`LegendFactService`/`FameDeriver` themselves — all confirmed
  correct and already shipped; this ticket only builds the missing delivery/consumption path.
- Any other item from the Dormant Mechanism Closure epic's own scope.
- Reviving every conceivable future signal source beyond what's confirmed real today — scope the
  `world_signals` set to what's actually shipped, not a speculative future framework.

## Acceptance Criteria
- [ ] `PerceptionUpdatePhase` has a real, live, non-test caller inside the Kernel's per-tick pipeline,
      at a deliberately chosen phase-ordering position (not an arbitrary slot).
- [ ] `MotivationBiasService.compute_bias_multiplier()` has a real, live, non-test caller feeding a
      real route/goal-scoring decision through the authoritative apply-path.
- [ ] A real test shows a `LegendFact`-derived signal producing a measurable route-bias shift for at
      least one Townsperson entity, through the real live pipeline (not a hand-called pure function).
- [ ] The Culture Drift bias overlay's own live-reachability is confirmed or explicitly disclosed if
      still gapped after this ticket's own wiring (don't assume it's automatically fixed without
      verifying).
- [ ] Determinism confirmed: no unsorted iteration over any new per-tick signal aggregation feeds a
      durable structure's key/iteration order (the same failure class this epic's own sibling ticket,
      `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`, already checked for its own bridge).

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (the sibling ticket this was split out of — idea 56's
  own bridge already landed independently and needs no rework regardless of this ticket's outcome)
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (idea 57's own shipped mechanism, the primary beneficiary)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/world/fame_legend_contract.md`
- `docs/world/culture_drift_contract.md` (the Culture Drift bias overlay's own contract)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/perception/phase.py`, `src/domains/perception/service.py`
- `src/domains/motivation/service.py`, `src/domains/motivation/resolver.py`, `src/domains/motivation/evaluator.py`
- `src/domains/culture/applicator.py` (`CulturalBiasApplicator`, E62C)
- `src/domains/fame/legend.py` (`LegendFactService.to_world_signal()`)
- `src/engine/kernel.py` (real phase ordering)

## Assumptions / Open Questions
- The exact real phase-ordering slot for `PerceptionUpdatePhase`, and the full v1 `world_signals` set,
  are not decided here — real architecture/design work for this ticket's own Investigate/Plan phases.
- Whether reviving this pipeline has any real performance-budget implications (a new per-tick phase)
  is not assessed here — confirm during Investigate against `docs/engine/performance_contract.md`'s
  hardware-class budgets.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
