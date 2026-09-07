---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE
phase: done
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE

## Title
Add Culture Drift as a new branch in the live personality_bias mechanism — bypass the dead Doctrine/Values chain entirely

## Status
DONE

Re-scoped 2026-09-07 per orchestrating-session decision, then implemented directly in the same
session (see Implementation Notes below for the full investigation that produced the decision, and
the real implementation).

**Decision, 2026-09-07 (RATIFIED — not open for re-litigation by whoever implements this):**
`MotivationBiasService.compute_bias_multiplier()`/`DoctrineResolver`/`IdentityDoctrine`/
`ValuePreferenceProfile` are confirmed-dead legacy code, superseded by the already-live
`personality_bias` mechanism in `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`,
lines ~206-223), which does the same conceptual job (personality/context → route-family bias) using
real, populated per-entity trait data. **Do not revive the Doctrine/Values chain.** Instead, add
Culture Drift's signal as a new branch directly inside `personality_bias`'s own existing
`route.family`-keyed pattern, mirroring its established style exactly. This also changes idea 57's
(Living Legend) own eventual integration point — see `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`,
which has been re-scoped to match.

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
- Bridge `CampaignState.region_cultures: Dict[str, CultureCarryForward]` into per-tick-reachable
  state, mirroring `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`'s own exact precedent: a new
  `AuthoritativeState.region_culture_states: Dict[str, CultureState]` field, populated once per
  episode by `CampaignOrchestrator._build_initial_state()` (sorted iteration for determinism).
- In `AdventureGoalScorer.score()` (`src/ai/goals/adventure_scorer.py:96` — confirmed the live,
  sole, unconditional per-tick adventure-decision call site with full `AuthoritativeState` access),
  resolve the entity's real region (`entity.navigation.region_id`) and look up the bridged
  `CultureState` for it (None-safe: no-op if the region has no culture-state entry yet).
- Thread the resolved `CultureState` down through `AdventureDecisionService.decide()`
  (`src/domains/adventure/service.py`) into `AdventureRouteScorer.score()`
  (`src/domains/adventure/scoring.py`) as a new parameter — confirm the real, minimal signature
  change needed during Investigate.
- Inside `AdventureRouteScorer.score()`'s existing `personality_bias` block (the `route.family`-keyed
  `if`/`elif` chain, lines ~206-223), add a new additive term computed from the bridged
  `CultureState` — reuse `CulturalBiasApplicator.compute_culture_delta(culture, tags)`'s own real
  logic/vocabulary (`"recovery"`/`"flee"`/`"caution"`, `"cooperation"`/`"help"`/`"party"`,
  `"exploration"`/`"research"`/`"intel"`/`"knowledge"`, `"gold"`/`"chest"`/`"loot"`/`"reward"` —
  confirmed via its own docstring example) mapped onto the real `RouteFamily` values already present
  in the same `if`/`elif` chain (e.g. `RECOVER` → `"recovery"`, `FORM_PARTY` → `"party"`/
  `"cooperation"`, `SELL_LOOT_FOR_GOLD` → `"gold"`/`"loot"`, `SCOUT_LOCATION`/`ASK_INFORMATION` →
  `"exploration"`/`"intel"`/`"knowledge"`) — a small, real mapping table, not a new tags data model.
  This is a change to a live, already-certified scoring formula — update `docs/mechanics/`/the
  parity ledger entry that documents `AdventureRouteScorer.score()` (confirm which entry during
  Investigate, likely in `strategic_cognition.yaml` or wherever route-scoring is already tracked).
- **Explicitly disclose, do not silently ignore**: `MotivationBiasService.compute_bias_multiplier()`,
  `DoctrineResolver`, `IdentityDoctrine`, and `ValuePreferenceProfile` are confirmed-dead legacy code,
  superseded by `personality_bias`, and are deliberately NOT revived by this ticket. Add a real
  disclosure (a docstring/comment at the dead code's own definition sites, plus a
  `docs/guidelines/intentional_divergences.md` entry per this repo's own convention for a deliberate
  behavior/architecture decision) rather than leaving future readers to wonder why a whole module
  went unused.
- Add real tests proving a non-default `CultureState` (real `faction_conflict_exposure`/other real
  fields) produces a measurably different `final_score` than the culture-absent baseline, through the
  real bridged pipeline — not a hand-called pure function.
- Given this touches a live, already-certified scoring formula and the live per-tick adventure-scoring
  call site, this ticket likely still warrants an `architecture-reviewer` pass on the Plan before
  Implementation, even with the redundancy question now resolved.

## Out of Scope
- Wiring `LegendFact` specifically — that is `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`'s own
  scope, sequenced after this ticket and re-scoped to target `personality_bias` too (not
  `compute_bias_multiplier()`).
- **Reviving `DoctrineResolver`/`IdentityDoctrine`/`ValuePreferenceProfile`/
  `MotivationBiasService.compute_bias_multiplier()`** — confirmed-dead, superseded legacy code per
  the ratified decision above. Disclose their dead status (see Scope); do not wire real callers for
  them, do not delete them either unless a separate, dedicated cleanup ticket decides to (deletion is
  a bigger, separate decision than this ticket's own scope — not deciding retirement-vs-dormant-
  documentation here beyond the disclosure itself).
- Reviving `PerceptionUpdatePhase` or wiring any `PerceptionModel` consumer — confirmed no real
  consumer need for it in this path.
- Adding a new `tags` field to `AdventureRouteOption` — no longer needed; the small
  `RouteFamily`-keyed mapping approach above avoids this data-model addition entirely.
- Rebuilding `CulturalBiasApplicator`/`AdventureRouteScorer`/`AdventureGoalScorer` themselves — all
  confirmed correct and already shipped; this ticket only adds one new branch/bridge.

## Acceptance Criteria
- [x] A real bridge carries `region_cultures`/`CultureState` from `CampaignState` into per-tick-
      reachable state at episode start (mirroring the idea-56 bridge precedent exactly).
- [x] `AdventureGoalScorer.score()` → `AdventureDecisionService.decide()` →
      `AdventureRouteScorer.score()` threads the bridged `CultureState` through to a new branch
      inside the existing `personality_bias` block, confirmed via a test showing a non-default
      `CultureState` producing a different `final_score` than the culture-absent baseline.
- [x] `MotivationBiasService`/`DoctrineResolver`/`IdentityDoctrine`/`ValuePreferenceProfile`'s
      confirmed-dead status is explicitly disclosed (docstring/comment + a real
      `intentional_divergences.md` entry) — not silently left unexplained.
- [x] Determinism confirmed: no unsorted iteration over any new per-tick aggregation feeds a durable
      structure's key/iteration order.
- [x] The parity ledger entry documenting `AdventureRouteScorer.score()`'s formula is updated to
      reflect the new Culture Drift branch, per the Authoritative Mechanics Rule.

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
- `src/core/state.py` (new `AuthoritativeState.region_culture_states` field)
- `src/domains/campaigns/orchestrator.py` (`CampaignOrchestrator._build_initial_state()`)
- `src/ai/goals/adventure_scorer.py` (`AdventureGoalScorer.score()`, the live call site)
- `src/domains/adventure/service.py` (`AdventureDecisionService.decide()`)
- `src/domains/adventure/scoring.py` (`AdventureRouteScorer.score()`'s `personality_bias` block)
- `src/domains/culture/applicator.py` (`CulturalBiasApplicator.compute_culture_delta()`, E62C — the
  real logic/vocabulary this ticket's new branch reuses)
- `src/domains/motivation/{resolver,service}.py`, `src/core/cognition.py` (`IdentityDoctrine`/
  `ValuePreferenceProfile`) — confirmed-dead legacy, disclosure only, not revived

## Assumptions / Open Questions
- The exact real `RouteFamily` → Culture Drift vocabulary mapping (which real `route.family` values
  map to which of `compute_culture_delta()`'s real tag strings) is not finalized here — real design
  work for this ticket's own Investigate/Plan phases, grounded in what's already established by
  `personality_bias`'s own existing `route.family`-keyed branches.
- Whether this new formula term has any real performance-budget implications is not assessed here —
  confirm during Investigate against `docs/engine/performance_contract.md`.
- Whether `DoctrineResolver`/`IdentityDoctrine`/`ValuePreferenceProfile`/
  `MotivationBiasService.compute_bias_multiplier()` should eventually be deleted outright (vs. left
  dormant-but-disclosed) is a separate, later decision — not resolved here, and not this ticket's
  own job to make.

## Implementation Notes

Implemented directly after the ratified decision, in one session, as the exact bridge+branch shape
described above:

1. **Bridge** (`src/core/state.py`, `src/domains/campaigns/orchestrator.py`): added
   `AuthoritativeState.region_culture_states: Dict[str, CultureState]`
   (`repr=False, compare=False`, mirroring `region_loyalty_pressure`'s own precedent). Populated
   once per episode in `CampaignOrchestrator._build_initial_state()` via a sorted-`.keys()`
   dict comprehension reading `self._state.region_cultures[region_id].culture`
   (`CultureCarryForward.culture: CultureState`) — same determinism discipline as the existing
   `region_loyalty_pressure` computation immediately above it.
2. **Real vocabulary correction**: the inherited ticket text (Scope, above) cited
   `compute_culture_delta()`'s tag vocabulary as including `"exploration"`/`"research"`/`"intel"`/
   `"knowledge"`/`"gold"`/`"chest"`/`"loot"`/`"reward"`. Reading the actual constants in
   `src/domains/culture/applicator.py` (`_FATALISM_POSITIVE`/`_FATALISM_NEGATIVE`/`_HERO_POSITIVE`/
   `_SCARCITY_POSITIVE`/`_CONFLICT_POSITIVE`/`_CONFLICT_NEGATIVE`) shows the real vocabulary is only
   `{caution, recovery, flee, pride, combat, aggressive, loyalty, party, survival}` — narrower than
   what was speculated. The new `_CULTURE_DRIFT_TAGS_BY_FAMILY` mapping in
   `src/domains/adventure/scoring.py` is grounded in this real vocabulary, not the ticket's
   inherited citation.
3. **Threading** (`src/domains/adventure/service.py`, `src/ai/goals/adventure_scorer.py`): added
   `culture_state: Optional[CultureState] = None` to `AdventureDecisionService.decide()` and threaded
   it into its own `AdventureRouteScorer.score()` call. `AdventureGoalScorer.score()` resolves
   `entity.navigation.region_id`, looks up `state.region_culture_states.get(region_id)` (None-safe:
   no region / no bridged entry both yield `None`, reproducing exact pre-bridge behavior), and passes
   it through `decide()`.
4. **New branch** (`src/domains/adventure/scoring.py`): a new, independent `if culture_state is not
   None:` block inside `AdventureRouteScorer.score()`'s `personality_bias` section, placed *after*
   the existing trait-based `if`/`elif` chain (not inside it — Culture Drift is additive/
   simultaneous with a trait match, not mutually exclusive with it). Looks up
   `_CULTURE_DRIFT_TAGS_BY_FAMILY.get(route.family)`; when present, adds
   `CulturalBiasApplicator.compute_culture_delta(culture_state, culture_tags)` (E62C, reused
   unchanged) to `personality_bias`.
5. **Dead-code disclosure**: added "CONFIRMED DEAD LEGACY CODE" notes to the module docstrings of
   `src/domains/motivation/resolver.py` (`DoctrineResolver`), `src/domains/motivation/service.py`
   (`MotivationBiasService`), and the class docstrings of `IdentityDoctrine`/`ValuePreferenceProfile`
   (`src/core/cognition.py`), each citing the real zero-caller/mathematically-inert evidence and
   cross-referencing the new `docs/guidelines/intentional_divergences.md` §2.53 entry (added to both
   the file's Divergence Summary Table and its Detailed Records section).
6. **Docs/parity**: `docs/parity_ledger/strategic_cognition.yaml` STRAT-227's `text`/`v2_evidence`/
   `test_path` fields updated in place via `tools/parity_ledger_writer.py::write_entry()` (surgical,
   schema-validated — not a full-file rewrite); `docs/mechanics/04_strategic_cognition.md` §6.4
   updated with a new "Culture Drift branch" subsection and mapping table.
7. Fixed a real, discovered regression: 6 pre-existing test files across `tests/unit/ai/goals/`,
   `tests/unit/strategic/`, and `tests/unit/observability/` define fixed-signature
   `AdventureDecisionService.decide()` test doubles (`_fake_decide`/`_spy_decide`) with no
   `culture_state` parameter and no `**kwargs`; threading the new keyword argument through the real
   call broke all of them with `TypeError: got an unexpected keyword argument 'culture_state'`. Added
   `culture_state=None` to each fake's signature (no behavior change to the fakes themselves — they
   already ignored unused kwargs conceptually, just couldn't accept this one syntactically).

## Test Summary
New tests:
- `tests/unit/domains/adventure/test_culture_drift_route_bias.py` (4 tests) — proves
  `AdventureRouteScorer.score()`'s new branch: raises `RECOVER`'s score when `fatalism` is above the
  activation threshold; no effect when all axes are below threshold; no effect for an unmapped
  `RouteFamily`; `culture_state=None` is identical to omitting the parameter.
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` (+2 tests) — proves the real bridge wiring
  end-to-end through `AdventureGoalScorer.score()`: a `CultureState` bridged for the entity's own
  `region_id` is threaded unchanged into `decide()`; missing `region_id` or an unbridged region both
  fall back to `None`, not a `KeyError`.

Regression: full scoped sweep across every test file touching this call chain —
`tests/unit/ai/`, `tests/unit/strategic/`, `tests/unit/observability/`,
`tests/unit/domains/adventure/`, `tests/unit/domains/campaigns/`, `tests/unit/domains/culture/`,
`tests/unit/domains/motivation/`, `tests/unit/motivation/`, `tests/integration/scenarios/
test_phase3_adventure_decision_scenarios.py`, `tests/integration/scenarios/
test_causal_memory_route_scoring_e2e.py`, `tests/integration/scenarios/
test_phase14_motivation_doctrine_scenarios.py`, `tests/integration/scenarios/
test_phase15_commitment_reputation_scenarios.py`, `tests/integration/scenarios/
test_phase18_cognition_hierarchy_e2e.py`, `tests/integration/campaigns/`,
`tests/architecture/test_adventure_routing_flag_inert.py`, `tests/architecture/
test_adventure_route_score_max_unchanged.py`, `tests/architecture/
test_fame_legend_fact_distinctness.py`, `tests/integration/domains/adventure/`,
`tests/perf/test_phase3_adventure_decision_budget.py` — **1714 passed, 1 skipped (pre-existing,
unrelated: a probabilistic real-500-tick recipe-learned event window), 0 failed**.

Determinism: the new bridge reuses the already-verified-deterministic `region_loyalty_pressure`
sorted-`.keys()` pattern exactly (self-corrected during implementation from an initial
`sorted(.items())` draft, which would have required Python to compare `CultureCarryForward` values
as a tiebreaker in the impossible event of equal keys — switched to `sorted(.keys())` + separate
lookup to remove even that latent fragility).

## Files Changed
- `src/core/state.py` — new `AuthoritativeState.region_culture_states` field
- `src/domains/campaigns/orchestrator.py` — populates the new field in `_build_initial_state()`
- `src/domains/adventure/scoring.py` — `_CULTURE_DRIFT_TAGS_BY_FAMILY` mapping + new
  `personality_bias` branch + `culture_state` parameter
- `src/domains/adventure/service.py` — threads `culture_state` through `decide()`
- `src/ai/goals/adventure_scorer.py` — resolves region + bridged `CultureState`, passes to `decide()`
- `src/domains/motivation/resolver.py`, `src/domains/motivation/service.py`, `src/core/cognition.py`
  — dead-code disclosure docstrings
- `docs/guidelines/intentional_divergences.md` — new §2.53 entry + summary table row
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-227 updated
- `docs/mechanics/04_strategic_cognition.md` — §6.4 updated
- `docs/REGISTRY.yaml` — regenerated (`make docs-registry`)
- New tests: `tests/unit/domains/adventure/test_culture_drift_route_bias.py`
- Fixed pre-existing test doubles (regression fix, no behavior change):
  `tests/unit/ai/goals/test_adventure_goal_scorer.py`,
  `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`,
  `tests/unit/observability/test_event_shapers_strategy.py`,
  `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`,
  `tests/unit/strategic/test_adventure_route_materialization.py`

## Completion Summary
Culture Drift (idea 57's own Culture-side signal, and the shared prerequisite for idea 57's
LegendFact half) now produces a real, measurable, tested effect on live adventure-route scoring —
without reviving the confirmed-dead Doctrine/Values chain. The dead chain itself is left dormant but
now explicitly disclosed (docstrings + `intentional_divergences.md` §2.53), not silently unexplained.
`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` can now proceed against this real `personality_bias`
integration point. Not pushed — left as local commits on `dormant-mechanism-closure` per this
session's own fork-execution constraints.

---

## Investigation History (2026-09-07, pre-decision — kept for evidence, not re-litigation)

The section below is the original investigation that led to the ratified decision above (Culture
Drift as a new `personality_bias` branch; `DoctrineResolver`/`IdentityDoctrine`/
`ValuePreferenceProfile`/`compute_bias_multiplier()` confirmed-dead, disclosed not revived). Every
citation in it was independently re-verified by the orchestrating session against real code before
the decision was made. Whoever implements this ticket should read it for the evidence, but the
decision itself is not open for re-litigation — implement per the Scope/AC above.

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

**Decision made 2026-09-07: option 1.** All citations above are independently reproducible via the
exact file:line references and grep commands cited, and were independently re-verified by the
orchestrating session before this decision was ratified.
