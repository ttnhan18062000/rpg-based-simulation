---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE
phase: open
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE

## Title
Build the real prerequisite infrastructure for route-bias scoring — wires DoctrineResolver, adds a tags field to AdventureRouteOption, adds a bias term to AdventureRouteScorer

## Status
BLOCKED — escalated 2026-09-07: `AdventureRouteScorer.score()` already has a separate, live,
already-shipped `personality_bias` term doing conceptually the same job this ticket's own
Doctrine/Values path would duplicate — see Implementation Notes. Real, buildable path exists for
the Culture Drift half of this ticket, but a real architecture/consolidation decision is needed
before writing code.

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Split out of `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` on 2026-09-07 (itself split out
of `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`, Dormant Mechanism Closure epic child 1). That
ticket's own investigation found idea 57's (Living Legend) real revival scope is a **4-component
dead chain plus a missing data model**, not the 2-component gap originally assumed:

1. **`DoctrineResolver.resolve()`** (`src/domains/motivation/resolver.py`) has zero real (non-test)
   callers anywhere in `src/` — confirmed via grep. `motivation.doctrine` on every real entity is
   always the bare default `IdentityDoctrine(class_id=...)` with **empty**
   `preferred_route_tags`/`avoided_route_tags`.
2. **`MotivationBiasService.compute_bias_multiplier()`** (`src/domains/motivation/service.py`) has
   zero real callers anywhere in `src/`. Even if wired, it would compute a no-op multiplier (1.0)
   for every real entity today, since nothing populates the doctrine it reads from (item 1).
3. **`AdventureRouteOption` has no `tags` field of any kind** (`src/domains/adventure/schema.py`) —
   only `family: RouteFamily`. `compute_bias_multiplier()`'s expected tag vocabulary (`"melee"`,
   `"ranged"`, `"heavy_armor"`, `"spells"`, `"flee"`, `"scouting"`, `"stealth"`, `"intel"`,
   `"mana"` — confirmed via `DoctrineResolver.resolve()`'s own real per-class data) does not overlap
   with `RouteFamily`'s vocabulary (`"recover"`, `"gather_resource"`, `"buy_upgrade"`,
   `"scout_location"`, etc. — only a near-miss: `"scout_location"` vs. `"scouting"`).
4. **`AdventureRouteScorer.score()`**'s real, live, already-certified formula (`src/domains/
   adventure/scoring.py:333`: `final_score = urgency + benefit + personality_bias +
   plan_advance_bonus + memory_adjustment + confidence_bonus - risk_penalty - blocker_penalty`) has
   **no existing bias/multiplier term at all** — confirmed via direct read.

This ticket builds the real, shared prerequisite infrastructure that benefits **both** idea 57
(Living Legend) and the already-built Culture Drift bias overlay (`CulturalBiasApplicator.
compute_culture_delta()`, `src/domains/culture/applicator.py`, E62C) — neither can ever produce a
real effect without this infrastructure existing first, regardless of which specific signal
eventually flows through it.

## Scope
- Wire `DoctrineResolver.resolve()` to a real, live call site — confirm during Investigate whether
  this should happen once at entity construction (keyed by `class_id`) or be re-resolved
  dynamically; ground the decision in how `IdentityDoctrine`'s own fields are meant to be used
  (read `DoctrineResolver`'s own docstring/tests for its original design intent).
- Add a `tags` field to `AdventureRouteOption` (or an equivalent real mechanism) that can carry a
  real, populated set of tags per route option. Decide the real vocabulary: reuse
  `IdentityDoctrine`'s combat-style vocabulary, introduce a new route-specific vocabulary, or
  support both — ground this decision in what `AdventureRouteGenerator`'s real route-construction
  call sites can actually populate today, not an invented ideal.
- Add a real bias/multiplier term to `AdventureRouteScorer.score()`'s existing formula, sourced from
  `MotivationBiasService.compute_bias_multiplier()` fed by the new `tags` field and the entity's
  (now-real) `IdentityDoctrine`. This is a change to a live, already-certified scoring formula —
  treat it with the same care as any Mechanics Bible formula change (update
  `docs/mechanics/`/parity ledger if this formula is documented there; confirm during Investigate).
- Confirm the Culture Drift bias overlay's own live-reachability once this infrastructure exists —
  `compute_bias_multiplier(entity, tags, culture_values)` already accepts a `culture_values`
  parameter designed for `CulturalBiasApplicator`'s output; wiring the real call site should make
  this reachable as a side effect, but verify directly, don't assume.
- Add real tests proving `DoctrineResolver` output reaches a real scored route, and that a non-empty
  `tags`/doctrine combination produces a measurably different `final_score` than the empty-doctrine
  baseline (a real regression-catching assertion, not a tautology).
- Given this touches a live, already-certified scoring formula and multiple subsystem boundaries
  (motivation → adventure route generation → scoring), this ticket likely warrants an
  `architecture-reviewer` pass on the Plan before Implementation.

## Out of Scope
- Wiring `LegendFact` specifically into this infrastructure — that is
  `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`'s own scope, sequenced after this ticket.
  This ticket only builds the shared prerequisite; it does not need to produce a Living-Legend
  specific test.
- Reviving `PerceptionUpdatePhase` or wiring any `PerceptionModel` consumer — the investigation that
  split this ticket out found no real code anywhere reads `PerceptionModel` fields for route
  generation/scoring, and `compute_bias_multiplier()` does not require `PerceptionUpdatePhase`'s
  output at all (it takes `culture_values`/`tags` directly, not a perception snapshot) — confirm
  this finding still holds during Investigate, but do not assume `PerceptionUpdatePhase` needs
  reviving as part of this ticket unless Investigate finds real evidence otherwise.
- Rebuilding `CulturalBiasApplicator`/`IdentityDoctrine`/`AdventureRouteScorer` themselves — all
  confirmed correct and already shipped; this ticket only builds the missing connective wiring.

## Acceptance Criteria
- [ ] `DoctrineResolver.resolve()` has a real, live, non-test caller.
- [ ] `AdventureRouteOption` (or an equivalent real mechanism) carries a real, populated tag/doctrine
      signal for at least one real route-generation call site.
- [ ] `MotivationBiasService.compute_bias_multiplier()` has a real, live, non-test caller feeding
      `AdventureRouteScorer.score()`'s formula, confirmed via a test showing a non-default doctrine
      value producing a different `final_score` than the empty-doctrine baseline.
- [ ] The Culture Drift bias overlay's own live-reachability is confirmed (or explicitly disclosed
      as still gapped, with a real reason) once this infrastructure exists.
- [ ] Determinism confirmed: no unsorted iteration over any new per-tick aggregation feeds a durable
      structure's key/iteration order.
- [ ] If `AdventureRouteScorer.score()`'s formula is documented in `docs/mechanics/` or the parity
      ledger, both are updated to reflect the new bias term, per the Authoritative Mechanics Rule.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` (`tickets/done/` — the investigation this
  was split out of; DONE with its own real deliverable being the investigation itself)
- `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` (the sibling ticket that depends on this one landing
  first)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (`tickets/done/` — idea 56's own, structurally
  unrelated bridge; no code overlap expected)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/world/culture_drift_contract.md` (the Culture Drift bias overlay's own contract)

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/motivation/resolver.py` (`DoctrineResolver`)
- `src/domains/motivation/service.py` (`MotivationBiasService.compute_bias_multiplier()`)
- `src/domains/adventure/schema.py` (`AdventureRouteOption`)
- `src/domains/adventure/scoring.py` (`AdventureRouteScorer.score()`)
- `src/domains/culture/applicator.py` (`CulturalBiasApplicator`, E62C)

## Assumptions / Open Questions
- The exact real vocabulary for the new `tags` field (reuse `IdentityDoctrine`'s combat-style
  vocabulary, a new route-specific one, or both) is not decided here — real design work for this
  ticket's own Investigate/Plan phases.
- Whether `DoctrineResolver.resolve()` should run once at construction or dynamically is not decided
  here.
- Whether this new formula term has any real performance-budget implications is not assessed here —
  confirm during Investigate against `docs/engine/performance_contract.md`.

## Implementation Notes

**Escalated, 2026-09-07 — no code written; this is a pure Investigate-phase finding, the 3rd round
of honest re-scoping for idea 57's revival chain.**

### The critical new finding: a live, shipped, redundant "personality bias" mechanism already exists

`AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`) already computes a real,
already-live `personality_bias` term (lines 206-223) — completely separate from
`MotivationBiasService.compute_bias_multiplier()`:

```python
personality_bias = 0.0
if route.family == RouteFamily.RECOVER:
    personality_bias += caution * 0.25
elif route.family in (RouteFamily.GATHER_RESOURCE, RouteFamily.SELL_LOOT_FOR_GOLD, RouteFamily.TAKE_EASY_QUEST):
    personality_bias += greed * 0.50
elif route.family in (RouteFamily.ASK_INFORMATION, RouteFamily.SCOUT_LOCATION):
    personality_bias += curiosity * 0.25
elif route.family in (RouteFamily.CRAFT_UPGRADE, RouteFamily.GATHER_RESOURCE):
    personality_bias += industry * 0.25
elif route.family == RouteFamily.FORM_PARTY:
    personality_bias += sociability * 0.40
elif route.family == RouteFamily.QUEST_OPPORTUNITY:
    personality_bias += greed * 0.50
```

This reads real, already-populated per-entity personality traits (`caution`/`greed`/`curiosity`/
`industry`/`sociability` — a live trait model, confirmed calibrated as recently as "E11C, 2026-06-28"
per its own inline comment) and maps `route.family` directly to a weighted bonus — **the exact same
conceptual job** (personality → route preference bias) that `MotivationBiasService.
compute_bias_multiplier()` was designed to do via `IdentityDoctrine`/`ValuePreferenceProfile`, using
a **different, real, already-live trait source** instead of the 100%-dead doctrine/values fields.

This is not a coincidence to route around — it means `compute_bias_multiplier()`/`DoctrineResolver`
are very likely **legacy/superseded Phase-14 code**, made redundant by whatever later phase shipped
the real `personality_bias` mechanism, not simply "unwired." Two independent findings support this:

1. **`DoctrineResolver.resolve()`'s only real class_id producer is narrow and isolated**:
   `class_id="warrior"` (or a value from `spec.actors.class_distribution`) is set at exactly one
   real call site, `SimulationAnalysisRunner.run()`'s own Hero-actor construction
   (`src/domains/campaigns/runner.py:70-81`, a single-episode Campaign-analysis tool, not the main
   corpus-world entity population path). No real corpus-world entity (Townspeople included) ever
   gets a `class_id` other than the bare default `"NOVICE"` — confirmed via repo-wide grep, zero
   other real `class_id_set=`/`identity(class_id=...)` call sites exist anywhere in `src/`.
2. **`ValuePreferenceProfile` (the "Value Preference Profile" half of `compute_bias_multiplier()`)
   is equally 100% unpopulated** — `survival`/`reward`/`knowledge`/`loyalty`/`pride`/`curiosity`/
   `caution` all default to exactly `0.5`, and the formula's own `(value - 0.5) * 0.5` terms are
   therefore mathematically guaranteed to evaluate to `0.0` for every real entity in the game today.
   Zero real construction of a non-default `ValuePreferenceProfile` exists anywhere in `src/`.

So `compute_bias_multiplier()` is not merely "missing one caller" — **all three of its real inputs
are simultaneously dead** (doctrine, values, and — until this ticket — culture), while a real, live,
differently-sourced mechanism already fills the same conceptual role in the same formula.

### The one genuinely buildable, disclosed-but-real path: Culture Drift, via `route.family`

Despite the above, one real, concrete, buildable path was found for the Culture Drift half of this
ticket specifically (not the Doctrine/Values half):

- `CampaignState.region_cultures: Dict[str, CultureCarryForward]` (`src/domains/culture/model.py`)
  — each `CultureCarryForward.culture: CultureState` already holds exactly the type
  `CulturalBiasApplicator.compute_culture_delta(culture: CultureState, tags: Iterable[str])` expects.
- `compute_culture_delta()`'s own docstring example (`tags=["caution", "recovery"]`) uses the SAME
  generic semantic vocabulary as `compute_bias_multiplier()`'s "Value Preference Profile" section
  (`"recovery"`/`"flee"`/`"caution"`, `"cooperation"`/`"help"`/`"party"`,
  `"exploration"`/`"research"`/`"intel"`/`"knowledge"`, `"gold"`/`"chest"`/`"loot"`/`"reward"`) — NOT
  `IdentityDoctrine`'s combat-style vocabulary (`"melee"`/`"ranged"`/`"heavy_armor"`). This vocabulary
  maps reasonably (if not perfectly) onto real `RouteFamily` enum values (e.g. `RECOVER` → `"recovery"`,
  `FORM_PARTY` → `"party"`/`"cooperation"`, `SELL_LOOT_FOR_GOLD` → `"gold"`/`"loot"`,
  `SCOUT_LOCATION`/`ASK_INFORMATION` → `"exploration"`/`"intel"`/`"knowledge"`) — meaning **no new
  `tags` field on `AdventureRouteOption` is actually needed**; a small static
  `RouteFamily -> frozenset[str]` mapping table (mirroring `personality_bias`'s own existing
  `route.family`-keyed `if`/`elif` pattern) would suffice.
- The real, live, unconditional, per-tick call site that has full `AuthoritativeState` access is
  `AdventureGoalScorer.score(self, entity: EntityState, state: AuthoritativeState)`
  (`src/ai/goals/adventure_scorer.py:96`) — confirmed via its own inline comment as "the live, sole
  adventure-decision path today... reached unconditionally, every tick, for every entity eligible."
  This is where an entity's real region (`entity.navigation.region_id`) could be resolved and a
  bridged `region_id -> CultureState` snapshot looked up, then threaded down through
  `AdventureDecisionService.decide()` (`src/domains/adventure/service.py`, needs a new
  `culture_values` parameter) into `AdventureRouteScorer.score()` (`src/domains/adventure/
  scoring.py`, needs the same) and finally into `compute_bias_multiplier()`.
- A bridge for this would exactly mirror `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`'s own
  precedent: a new `AuthoritativeState.region_culture_states: Dict[str, CultureState]` field,
  populated once per episode by `CampaignOrchestrator._build_initial_state()` from
  `CampaignState.region_cultures` (`{region_id: cf.culture for region_id, cf in sorted(...)}`,
  sorted for determinism).

### Why this still needs a real decision before implementation, not a unilateral fix

Implementing the Culture Drift path above would technically satisfy this ticket's AC4 (Culture Drift
live-reachability) and partially satisfy AC3 (`compute_bias_multiplier()` gets a real caller), but:
- It would leave `DoctrineResolver`/`IdentityDoctrine` (AC1) and `ValuePreferenceProfile` permanently
  dead regardless — not fixed by this path, and per the finding above, very likely SHOULD stay dead
  (superseded by the real `personality_bias` mechanism) rather than be revived for its own sake.
- Whether `MotivationBiasService.compute_bias_multiplier()` should be (a) kept as a real, live,
  Culture-Drift-only mechanism running alongside `personality_bias` in the same formula (two
  additive bias terms with different real inputs), (b) deprecated/removed as dead, superseded code
  with the Culture Drift signal instead added as a NEW branch directly inside `personality_bias`'s
  own existing `route.family`-keyed pattern (reusing real, live personality traits, not reviving
  `IdentityDoctrine`/`ValuePreferenceProfile` at all), or (c) something else, is a genuine
  architecture/product decision this ticket's own text did not anticipate and a hand-orchestrating
  implementer should not decide alone — it determines whether real, redundant, dead code
  (`DoctrineResolver`, `IdentityDoctrine`, `ValuePreferenceProfile`) gets left in the codebase
  indefinitely or is explicitly retired.
- This also changes idea 57's (Living Legend) own eventual integration point: if the answer is (b),
  `LegendFact`'s own bias should likely be added as a new branch in `personality_bias`'s existing
  pattern too, not through `compute_bias_multiplier()`/`MotivationBiasService` at all — meaning
  `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`'s own scope may need revision once this decision is
  made.

### Recommendation

Do not implement this ticket as currently scoped, and do not implement even the narrower
"Culture-Drift-only" path without an explicit decision on the `personality_bias` vs.
`compute_bias_multiplier()` redundancy question above. Real options:
1. **Add Culture Drift as a new branch in the existing, real, live `personality_bias` mechanism**
   directly (reusing real personality traits' existing pattern, e.g. a new additive term computed
   from the entity's region `CultureState` via a small new helper mirroring
   `compute_culture_delta()`'s own logic) — bypasses `MotivationBiasService`/`DoctrineResolver`/
   `IdentityDoctrine`/`ValuePreferenceProfile` entirely, treating them as confirmed-dead legacy code
   not worth reviving. Smallest real diff; matches what's actually live today.
2. **Wire Culture Drift through `compute_bias_multiplier()` as a real, live, Culture-only mechanism**
   running alongside `personality_bias` (leaving `DoctrineResolver`/`IdentityDoctrine`/
   `ValuePreferenceProfile` explicitly disclosed as dead-but-intentionally-unrevived) — keeps the
   existing `MotivationBiasService` module meaningfully alive rather than fully bypassed, at the
   cost of two structurally-similar-but-separate bias mechanisms coexisting in the same formula.
3. **File a dedicated cleanup/consolidation ticket first** (retire or fully revive
   `DoctrineResolver`/`IdentityDoctrine`/`ValuePreferenceProfile` as a real, separate decision),
   before either of the above, since that question is orthogonal to whether Culture Drift itself
   becomes live.

No code, docs, or test changes were made — this Implementation Notes section IS the deliverable of
this Investigate-phase pass. All citations above are independently reproducible via the exact
file:line references and grep commands cited.

## Test Summary
No tests run — no code changed.

## Files Changed
None.

## Completion Summary
(Not completed — escalated per Implementation Notes above. A real, buildable path for the Culture
Drift half of this ticket was found, but implementing it requires a prior decision on whether
`MotivationBiasService`/`DoctrineResolver` are redundant legacy code (superseded by the already-live
`personality_bias` mechanism) or should be kept alive as a parallel system — not decided here.)
