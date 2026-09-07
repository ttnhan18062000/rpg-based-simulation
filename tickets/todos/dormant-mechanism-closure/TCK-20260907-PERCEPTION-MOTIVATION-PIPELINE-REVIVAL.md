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
BLOCKED — escalated 2026-09-07, real scope is a 4-component dead chain plus a missing data model, not the 2-component gap originally scoped (see Implementation Notes)

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

**Escalated, 2026-09-07 — the real scope is materially larger than this ticket's own Request
Summary anticipated. No code was written; this is a pure Investigate-phase finding.**

### The real chain has 4 dead links, not 2

This ticket's own Request Summary named 2 dead functions (`PerceptionUpdatePhase`,
`MotivationBiasService.compute_bias_multiplier()`). Direct investigation found **2 more, plus a
missing data model, forming one unbroken dead chain from end to end**:

1. **`DoctrineResolver.resolve()`** (`src/domains/motivation/resolver.py`) — has **zero real
   (non-test) callers anywhere in `src/`**, confirmed via grep (only referenced from
   `motivation/__init__.py`'s own re-export and test files). This means `motivation.doctrine` on
   every real entity is always the bare default `IdentityDoctrine(class_id=...)` with **empty**
   `preferred_route_tags`/`avoided_route_tags` — the exact fields
   `compute_bias_multiplier()` reads. Even if `compute_bias_multiplier()` were wired to a real
   caller today, it would compute a no-op multiplier (1.0) for every real entity, because nothing
   ever populates the doctrine it reads from.
2. **`PerceptionUpdatePhase`** (`src/domains/perception/phase.py`) — confirmed zero real callers
   (as this ticket's own Request Summary already stated). It produces an updated `PerceptionModel`
   (`perceived_entities`/`perceived_resources`/`perceived_opportunities`/`perceived_threats`/etc.)
   on the entity.
3. **No real code anywhere reads `PerceptionModel`'s fields for route generation or scoring** —
   confirmed via grep across `src/domains/adventure/` (route generation/scoring) and
   `src/systems/strategic_systems/` (strategic pass): zero hits for `perceived_opportunities`,
   `perceived_threats`, or `PerceptionModel` outside `src/domains/perception/` itself. Even if
   `PerceptionUpdatePhase` were wired into the live tick loop, its output would still go nowhere —
   there is no existing consumer to connect it to.
4. **`MotivationBiasService.compute_bias_multiplier()`** — confirmed zero real callers (as this
   ticket's own Request Summary already stated). Its `tags: Iterable[str]` parameter expects a
   **combat/tactical-style vocabulary** (`"melee"`, `"ranged"`, `"heavy_armor"`, `"spells"`,
   `"flee"`, `"scouting"`, `"stealth"`, `"intel"`, `"mana"` — confirmed via
   `DoctrineResolver.resolve()`'s own real per-class doctrine data and
   `tests/unit/domains/motivation/test_phase14_bias_service.py`), **not** the `RouteFamily` enum
   vocabulary (`"recover"`, `"gather_resource"`, `"buy_upgrade"`, `"scout_location"`, etc.) that
   `AdventureRouteOption` actually carries via its `family` field. **`AdventureRouteOption` has no
   `tags` field of any kind** (confirmed via direct read of `src/domains/adventure/schema.py`) —
   there is no existing data model that would let a real route ever be scored against
   `compute_bias_multiplier()`'s expected tag vocabulary at all. The two tag vocabularies do not
   overlap (only a near-miss: `"scout_location"` vs. `"scouting"`) and represent genuinely
   different classification dimensions (WHAT to do vs. HOW to fight) — there is no cheap, already-
   implied mapping between them to build on.

### Why this is a genuine architectural fork, not a small wiring gap

Reviving idea 57 (and the Culture Drift bias overlay) "as scoped" would require design decisions on
at least 4 independent axes, each with real trade-offs the ticket's own text does not resolve and
that a hand-orchestrating implementer should not decide alone:
- **Where/whether to wire `DoctrineResolver.resolve()`** — at entity construction (once, per
  `class_id`), or dynamically. If never wired, `compute_bias_multiplier()` can never produce a
  non-trivial multiplier for any doctrine-driven route no matter what else is built.
- **Whether `PerceptionUpdatePhase` is even on the real critical path for idea 57 at all.**
  `compute_bias_multiplier(entity, tags, culture_values)` takes `culture_values: CultureState`
  directly — it does NOT take a `PerceptionModel`. A `LegendFact`-driven bias could plausibly be
  wired to `compute_bias_multiplier()` without ever touching `PerceptionUpdatePhase`, by inventing
  a parallel `legend_values`-shaped input (mirroring `culture_values`) rather than going through
  perception filtering at all — a real, different design than "revive `PerceptionUpdatePhase`,"
  the design this ticket's own Scope assumed. Conversely, if `PerceptionUpdatePhase` genuinely is
  the intended real path (its own docstring says "Phase 12," implying original intent to wire it
  into the live pipeline), that's a separate, larger question about what its *other* real consumers
  should be (idea 57 alone doesn't justify reviving a whole phase whose other purpose — populating
  `perceived_entities`/`perceived_threats` for combat/social AI — has never been used by anything
  either).
- **Whether/how to invent a real `tags` field on `AdventureRouteOption`, and what its real
  vocabulary should be** — this is new data-model design work, not just wiring, and needs a
  decision on whether it should reuse the combat-style vocabulary `IdentityDoctrine` already uses,
  a new route-specific vocabulary, or both.
- **Where the real live route/goal-scoring call site should invoke `compute_bias_multiplier()`** —
  the real, live, already-shipped scorer (`AdventureRouteScorer.score()`,
  `src/domains/adventure/scoring.py`) has its own real, independent formula (`final_score =
  urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment +
  confidence_bonus - risk_penalty - blocker_penalty`) with **no existing bias/multiplier term at
  all** — adding one is a real change to a live, already-certified formula, not an additive no-op
  the way idea 56's own `region_loyalty_pressure` bridge was (a genuinely new, previously-`0.0`
  parameter with no existing formula to touch).

None of these four decisions is this ticket's own text resolved in advance, and guessing at any one
of them (e.g., inventing a route-tags vocabulary, or deciding `PerceptionUpdatePhase` is or isn't
on the critical path) would be exactly the kind of unilateral architecture decision this session's
own established discipline says to escalate rather than force.

### Recommendation

Do not implement this ticket as currently scoped. Real options for whoever tracks this epic next:
1. **Split further**: separate "wire `DoctrineResolver` + add a minimal `tags` field to
   `AdventureRouteOption` + add a bias term to `AdventureRouteScorer.score()`" (the real
   prerequisite infrastructure, benefits BOTH idea 57 and Culture Drift) from "wire `LegendFact`
   specifically into whatever that infrastructure turns out to be" (idea 57's own narrow piece).
2. **Re-scope narrower**: skip `PerceptionUpdatePhase` and route generation/scoring entirely; wire
   `LegendFact` → a new, `culture_values`-shaped `legend_values` input on
   `compute_bias_multiplier()` → a single, hand-picked existing decision point (e.g. directly
   inside `StrategicIntelligenceSystem.fused_strategic_pass()`, already real and live) — smaller,
   but bypasses `PerceptionUpdatePhase` and the route-scoring layer entirely, which may or may not
   match idea 57's own original design intent (re-read `TCK-20260905-FAME-DERIVER-LEGEND-FACT`
   closely before choosing this).
3. **Accept this really is epic-sized** and scope a proper multi-ticket mini-epic for the whole
   route-bias-scoring revival, treating idea 57/Culture Drift as two of several beneficiaries.

No code, docs, or test changes were made — this Implementation Notes section IS the deliverable of
this Investigate-phase pass.

## Test Summary
No tests run — no code changed. All grep-based investigation results above are independently
reproducible via the exact commands cited.

## Files Changed
None.

## Completion Summary
(Not completed — escalated per Implementation Notes above.)
