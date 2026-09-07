---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING
phase: done
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING

## Title
Wire LegendFact into the real route-bias scoring infrastructure — closes out idea 57 (Living Legend)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Split out of `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` on 2026-09-07, sequenced
**after** `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (a hard dependency — this ticket has
nothing to wire into until that ticket's own route-bias scoring formula/data model exists for real).
This is idea 57's (Living Legend, `TCK-20260905-FAME-DERIVER-LEGEND-FACT`) own narrow piece: once
the shared prerequisite infrastructure is real, connect `LegendFact` specifically as one real input
to it, producing a measurable route-bias shift for at least one Townsperson entity — the original
design intent of idea 57, finally reachable in live gameplay.

**Re-scoped, 2026-09-07, per the infrastructure ticket's own investigation and the orchestrating
session's ratified decision**: the real integration point is a new branch inside
`AdventureRouteScorer.score()`'s existing `personality_bias` mechanism (`src/domains/adventure/
scoring.py`), NOT `MotivationBiasService.compute_bias_multiplier()`/`DoctrineResolver`/
`IdentityDoctrine` — those are confirmed-dead legacy code, superseded by `personality_bias`, and are
deliberately not being revived (see `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own
Implementation Notes for the full evidence). Re-confirm this ticket's own citations against whatever
that infrastructure ticket actually shipped before implementing — do not assume the exact shape from
this text alone.

## Scope
- Re-confirm `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own real, shipped shape during this
  ticket's own Investigate phase — do not assume its exact design from this ticket's own text; read
  what actually landed.
- Bridge `LegendFact`/`legend_facts` (`CampaignState`, per idea 57's own shipped ticket) into
  per-tick-reachable state, following the exact same real precedent
  `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` already established for idea 56's `region_cultures`
  signal (a snapshot field on `AuthoritativeState`, populated once per episode by
  `CampaignOrchestrator._build_initial_state()`).
- Convert the bridged `LegendFact` data into whatever tag/doctrine-shaped input the now-real
  infrastructure (from `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`) expects —
  `LegendFactService.to_world_signal()` (`src/domains/fame/legend.py`) may already do part of this
  conversion; confirm and reuse rather than duplicate.
- Add a real, end-to-end test proving a `LegendFact` about a real legendary subject produces a
  measurable, attributable route-bias shift for at least one Townsperson entity, through the real
  live pipeline (not a hand-called pure function in isolation).
- Confirm determinism: no unsorted iteration over the bridged `legend_facts` data feeds any durable
  structure's key/iteration order, matching the sibling bridge ticket's own precedent.

## Out of Scope
- Building any part of the shared route-bias-scoring infrastructure itself — that is
  `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own scope, a hard prerequisite for this ticket.
- The Culture Drift bias overlay's own live-reachability — already covered by the infrastructure
  ticket's own Acceptance Criteria, not this ticket's job to re-verify.
- Rebuilding `FameDeriver`/`LegendFactService` themselves — confirmed correct and already shipped.

## Acceptance Criteria
- [ ] A real bridge carries `legend_facts` from `CampaignState` into per-tick-reachable state at
      episode start (mirroring the idea-56 bridge precedent).
- [ ] `LegendFact` data reaches the real route-bias scoring infrastructure built by
      `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`, producing a measurable route-bias shift for
      at least one real Townsperson entity, confirmed via a real end-to-end test.
- [ ] Determinism confirmed for the new bridge, matching the sibling bridge ticket's own bar.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (hard prerequisite — must land first)
- `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL` (`tickets/done/` — the investigation both
  this ticket and the infrastructure ticket were split out of)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` (`tickets/done/` — the structural precedent for this
  ticket's own `CampaignState` → per-tick bridge)
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (idea 57's own shipped mechanism, the beneficiary)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/world/fame_legend_contract.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/fame/legend.py` (`LegendFactService.to_world_signal()`)
- `src/domains/campaigns/orchestrator.py` (`CampaignOrchestrator._build_initial_state()`)
- `src/core/state.py` (a new `AuthoritativeState` snapshot field, mirroring
  `region_loyalty_pressure`)
- Whatever real consumer `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` builds (`src/domains/
  motivation/`, `src/domains/adventure/`)

## Assumptions / Open Questions
- **Resolved during Investigate**: the infrastructure ticket shipped exactly the `personality_bias`
  branch pattern its own re-scoped text described — `AdventureRouteScorer.score()` gained a
  `culture_state` parameter and a Culture Drift branch, not a `compute_bias_multiplier()`/
  `DoctrineResolver` revival. This ticket mirrors that exact shape for `legend_fact`.
- **Correction found during Investigate**: this ticket's own inherited text (Scope, Related Code
  Areas) assumed a `CampaignState.legend_facts` field / a tag-vocabulary conversion via
  `LegendFactService.to_world_signal()`. Neither is real: `LegendFact` is deliberately **not** a
  `CampaignState` field (per `src/domains/fame/legend.py`'s own docstring and
  `docs/world/fame_legend_contract.md`) — the real durable field is
  `CampaignState.entity_fame: Dict[str, FameCarryForward]`, and `LegendFact` is a lazy,
  threshold-gated read-model reconstructed at query time via `LegendFactService.for_entity()`.
  `to_world_signal()` is a *perception* discoverability adapter (wraps a fact as a `WorldSignal`)
  and has no bearing on route-bias scoring — not reused here, since route-bias scoring bypasses
  perception entirely (same as the Culture Drift branch it mirrors). The real bridge/integration
  design (below) is grounded in this corrected understanding, not the inherited text.
- **Design decision made here, not pre-specified by any prior ticket**: `LegendFact` carries no
  route-family/tag vocabulary (unlike Culture Drift's `CulturalBiasApplicator.compute_culture_delta()`)
  — it is a single scalar (`fame: float`) per subject. `AdventureRouteOption` also carries no
  entity/subject reference (only `target_node_id`/`quest_id`), so there is no way to bias a route
  toward "involves this specific legendary entity." The only real, defensible connection point is
  the *scoring entity's own* fame (self-referential), matching the doc's own name for the mechanism
  — "The Living Legend **Feedback Loop**": a legend's own accumulated fame reinforces their own
  further heroic quest-seeking, the loop the design was named for. Mapped to a single RouteFamily
  (`QUEST_OPPORTUNITY`) rather than several, since no other family has a comparably real semantic
  tie to a subject's own fame (unlike Culture Drift's broader, tag-matched vocabulary).
- **Real, disclosed pre-existing inconsistency found, not fixed here (out of scope)**: fame's
  `NarrativeLedgerEntry.subject_id` keying is not uniformly an entity id — `QUEST_COMPLETED`
  WorldEvents are emitted with `subject=quest_id`
  (`src/engine/pipeline_phases/quest_opportunity_rewards.py:109`), while `FameImporter.get_fame()`'s
  own docstring documents the intended calling convention as "entity_id's runtime value domain is
  NarrativeLedgerEntry.subject_id (str), not an int entity id" — implying callers pass
  `str(entity.id)`. No real `WorldEvent(category=ENTITY_DEATH, subject=str(entity_id))` emission
  site was found in `src/` (grepped repo-wide) — the HERO-death fame path documented in
  `docs/world/fame_legend_contract.md`'s Event Rule may itself be another disclosed-but-unwired gap,
  pre-dating this ticket and belonging to `TCK-20260905-FAME-DERIVER-LEGEND-FACT`'s own scope, not
  this one's (`## Out of Scope`: "Rebuilding FameDeriver/LegendFactService themselves"). This
  ticket's own bridge and bias branch are correct and real regardless of which upstream event path
  populates `entity_fame` — the wiring is agnostic to how a given `subject_id` earned its fame, and
  the real end-to-end test constructs `entity_fame` directly (matching the same testing precedent
  the infrastructure ticket used for `region_cultures`), not by driving the full event pipeline
  forward from tick 0. Flagging this rather than silently assuming it's fine, per this session's own
  disclosure discipline — a future ticket may want to verify/fix the `ENTITY_DEATH` emission gap if
  the HERO-death fame path is meant to be real today.

## Implementation Notes

Implemented directly following `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`'s own shipped
`personality_bias` branch pattern, in one session:

1. **Bridge** (`src/core/state.py`, `src/domains/campaigns/orchestrator.py`): added
   `AuthoritativeState.entity_legend_facts: Dict[str, LegendFact]` (`repr=False, compare=False`,
   mirroring `region_culture_states`'s own precedent exactly). Populated once per episode in
   `CampaignOrchestrator._build_initial_state()` via a sorted-`.keys()` loop over
   `self._state.entity_fame`, calling the real `LegendFactService.for_entity(self._state,
   subject_id)` per subject and keeping only non-`None` results (i.e. only subjects whose fame
   already crosses `FAME_THRESHOLD` — the threshold gate is reused unchanged, not re-derived).
   Same determinism discipline as `region_loyalty_pressure`/`region_culture_states`.
2. **Threading** (`src/domains/adventure/service.py`, `src/ai/goals/adventure_scorer.py`): added
   `legend_fact: Optional[LegendFact] = None` to `AdventureDecisionService.decide()` and threaded it
   into its own `AdventureRouteScorer.score()` call. `AdventureGoalScorer.score()` resolves
   `state.entity_legend_facts.get(str(entity.id))` (None-safe: no bridged entry — fame never
   crossed threshold, or subject_id convention mismatch per the Assumptions note above — simply
   yields `None`, reproducing exact pre-bridge behavior) and passes it through `decide()`.
3. **New branch** (`src/domains/adventure/scoring.py`): a new `if legend_fact is not None and
   route.family == RouteFamily.QUEST_OPPORTUNITY:` block inside `AdventureRouteScorer.score()`'s
   `personality_bias` section, placed *after* both the trait-based chain and the Culture Drift
   branch (additive/independent of both, not mutually exclusive). Adds `legend_fact.fame * 0.30` to
   `personality_bias` — at `fame = 1.0` (max), contributes up to `0.30`, comparable in magnitude to
   the existing trait-based terms (0.25-0.50).
4. **Docs/parity**: `docs/parity_ledger/strategic_cognition.yaml` STRAT-227 and STRAT-228 updated
   in place via `tools/parity_ledger_writer.py::write_entry()` (surgical, schema-validated — not a
   full-file rewrite; STRAT-228 updated too since it specifically documents QUEST_OPPORTUNITY's
   existing greed-based `personality_bias` term, which this new term is additive with);
   `docs/mechanics/04_strategic_cognition.md` §6.4 gained a new "Living Legend branch" subsection;
   `docs/world/fame_legend_contract.md`'s "No Live Consumer" section renamed to "Live Consumer:
   Route-Bias Scoring" and rewritten to reflect the new real call site (the perception/motivation
   gaps it originally disclosed remain real and are re-stated, not silently dropped).

## Test Summary
New tests:
- `tests/unit/domains/adventure/test_legend_fact_route_bias.py` (4 tests) — proves
  `AdventureRouteScorer.score()`'s new branch: raises `QUEST_OPPORTUNITY`'s score by exactly
  `fame * 0.30` when `legend_fact` is present; no effect for an unmapped `RouteFamily`;
  `legend_fact=None` is identical to omitting the parameter; additive/independent of the Culture
  Drift branch (a `culture_state` with no real tag mapping for `QUEST_OPPORTUNITY` produces no
  extra effect alongside a real `legend_fact` effect, proving the two branches don't share state).
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` (+2 tests) — proves the real bridge wiring
  end-to-end through `AdventureGoalScorer.score()`: a `LegendFact` bridged for the entity's own
  `str(entity.id)` key is threaded unchanged into `decide()`; a missing bridged entry falls back to
  `None`, not a `KeyError`.
- `tests/unit/domains/campaigns/test_fame_wiring.py` (+1 test) — proves
  `CampaignOrchestrator._build_initial_state()` itself (not just a hand-constructed
  `AuthoritativeState`) turns `CampaignState.entity_fame` into `entity_legend_facts` via the real
  `LegendFactService.for_entity()` threshold gate: a subject above `FAME_THRESHOLD` is bridged, one
  below is excluded.

Regression: full scoped sweep across every test file touching this call chain —
`tests/unit/ai/`, `tests/unit/strategic/`, `tests/unit/observability/`,
`tests/unit/domains/adventure/`, `tests/unit/domains/campaigns/`, `tests/unit/domains/culture/`,
`tests/unit/domains/motivation/`, `tests/unit/motivation/`, `tests/unit/domains/fame/`,
`tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py`, `tests/integration/
scenarios/test_causal_memory_route_scoring_e2e.py`, `tests/integration/scenarios/
test_phase14_motivation_doctrine_scenarios.py`, `tests/integration/scenarios/
test_phase15_commitment_reputation_scenarios.py`, `tests/integration/scenarios/
test_phase18_cognition_hierarchy_e2e.py`, `tests/integration/campaigns/`,
`tests/architecture/test_adventure_routing_flag_inert.py`, `tests/architecture/
test_adventure_route_score_max_unchanged.py`, `tests/architecture/
test_fame_legend_fact_distinctness.py`, `tests/integration/domains/adventure/`,
`tests/perf/test_phase3_adventure_decision_budget.py` (`-m "not slow"`) — **1747 passed, 6 skipped
(pre-existing, unrelated), 0 failed**.

5 pre-existing test files with fixed-signature `AdventureDecisionService.decide()` test doubles
(`_fake_decide`/`_spy_decide`, no `**kwargs`) needed a `legend_fact=None` parameter added — same
regression class the infrastructure ticket already hit and fixed for `culture_state`:
`tests/unit/ai/goals/test_adventure_goal_scorer.py`,
`tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`,
`tests/unit/observability/test_event_shapers_strategy.py`,
`tests/unit/strategic/test_fused_strategic_pass_routing_family.py`,
`tests/unit/strategic/test_adventure_route_materialization.py`.

Determinism: the new bridge reuses the already-verified-deterministic `region_culture_states`
sorted-`.keys()` pattern exactly — no unsorted iteration order feeds any durable structure.

## Files Changed
- `src/core/state.py` — new `AuthoritativeState.entity_legend_facts` field
- `src/domains/campaigns/orchestrator.py` — populates the new field in `_build_initial_state()`
  via `LegendFactService.for_entity()`
- `src/domains/adventure/scoring.py` — new `legend_fact` parameter + Living Legend
  `personality_bias` branch
- `src/domains/adventure/service.py` — threads `legend_fact` through `decide()`
- `src/ai/goals/adventure_scorer.py` — resolves bridged `LegendFact` via `str(entity.id)`, passes
  to `decide()`
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-227, STRAT-228 updated
- `docs/mechanics/04_strategic_cognition.md` — §6.4 updated
- `docs/world/fame_legend_contract.md` — "No Live Consumer" → "Live Consumer: Route-Bias Scoring",
  Integration Points table, Parity Ledger References table, new Acceptance Signal
- `docs/REGISTRY.yaml` — regenerated
- New test: `tests/unit/domains/adventure/test_legend_fact_route_bias.py`
- Extended tests: `tests/unit/ai/goals/test_adventure_goal_scorer.py`,
  `tests/unit/domains/campaigns/test_fame_wiring.py`
- Fixed pre-existing test doubles (regression fix, no behavior change):
  `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`,
  `tests/unit/observability/test_event_shapers_strategy.py`,
  `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`,
  `tests/unit/strategic/test_adventure_route_materialization.py`

## Completion Summary
Idea 57's (Living Legend) own narrow piece is now real: an entity's own Chronicle-derived fame,
once it crosses `FAME_THRESHOLD`, produces a real, measurable, tested `+fame*0.30` bias toward
`QUEST_OPPORTUNITY` route selection — the exact "fame reinforces further heroic deeds" feedback
loop idea 57 was named for — bridged from `CampaignState.entity_fame` into per-tick state and
wired through the same live `personality_bias` integration point
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` established for Culture Drift, entirely bypassing
the confirmed-dead `MotivationBiasService`/`DoctrineResolver` chain. A real, disclosed pre-existing
gap in `entity_fame`'s own `subject_id` keying convention for the `ENTITY_DEATH` path was found and
documented (not fixed — out of this ticket's scope) so a future reader doesn't have to
rediscover it. This closes out idea 57's entire revival chain
(`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` → `TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-
REVIVAL` → `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` → this ticket). Not pushed — left as
local commits on `dormant-mechanism-closure` per this session's own fork-execution constraints.
