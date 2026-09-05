---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260905-FAME-DERIVER-LEGEND-FACT
phase: done
date: 2026-09-05
tags: [social, strategy]
---

# TCK-20260905-FAME-DERIVER-LEGEND-FACT

## Title
Idea 57 — The Living Legend Feedback Loop (FameDeriver + LegendFact)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 57 (The Living Legend Feedback Loop, docs/brainstorm/rpg_feature_atlas.html) proposes that once a hero's Chronicle-recorded fame crosses a threshold, it becomes a discoverable fact other entities can perceive and weigh into their Motivation & Doctrine. A design doc (docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md, already merged via PR #126) fully works out the aggregation-shape half: a FameDeriver/FameState/FameCarryForward/FameExporter/FameImporter 5-piece structure mirroring CultureDeriver's exact 3-layer pattern (src/domains/culture/deriver.py, model.py, exporter.py), keyed by NarrativeLedgerEntry.subject_id instead of payload['region_id']. It recommends Option B for which events feed fame: quest_completed entries (subject-attributed) plus entity_death where the deceased was entity_role==HERO (posthumous fame, reusing CultureDeriver's own existing hero_veneration event-type rule) -- explicitly NOT capturing in-life combat-earned fame, since no combat_victory event type exists in the Narrative Ledger today (a disclosed, accepted limitation, not silently worked around). This ticket implements that design as-is (already reviewed and merged, authoritative for its own scope) plus idea 57's own remaining scope: a new LegendFact class and fame_threshold's numeric value. Investigation (2026-09-05) found a real honesty gap in the epic doc's original framing of the remaining scope: "Perception-system discoverability wiring so Motivation & Doctrine can weigh a specific hero's fame" targets two systems confirmed DORMANT in the live pipeline today -- PerceptionUpdatePhase (zero call sites in AuthoritativeApplyPipeline.refine(), per docs/simulation/domains/perception_contract.md and TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION) and MotivationBiasService.compute_bias_multiplier (zero call sites anywhere outside its own module, confirmed by grep). Additionally, idea 34's real implemented candidate-role set (src/ai/coming_of_age.py, _CANDIDATE_ROLES = (SHOPKEEPER, WORKER, GUARD)) has no ADVENTURER/HERO option to bias toward at all -- the illustrative "lean toward becoming an adventurer" scenario cannot be mechanically realized today without a separate, larger extension to idea 34's own candidate set, which is out of this ticket's scope.

## Scope
- Implement FameDeriver.derive(hierarchy, entity_names=None) -> Dict[str, FameState], keyed by entry.subject_id, summing entry.significance for quest_completed entries plus entity_death entries where payload['entity_role']=='HERO' (Option B), normalised via min(1.0, raw/NORMALISE_DENOMINATOR) exactly mirroring CultureDeriver._normalise -- per the already-merged design doc, verbatim.
- Implement FameState (frozen dataclass, new module e.g. src/domains/fame/model.py per the design doc's own reasoning for a new module over reusing culture/) and FameCarryForward (entity_id + FameState + derived_episode), mirroring CultureCarryForward's exact shape. Resolve the open axis-count question (single fame axis vs. fame+notoriety split mirroring SocialUpdate.heroism_delta/notoriety_delta) as a Plan-phase decision, documented with rationale.
- Implement FameExporter.export(campaign_state, hierarchy, episode_index, entity_names), called from the same CampaignOrchestrator._advance_state() episode-boundary call site as CultureDriftExporter.export() (orchestrator.py, alongside the existing call), writing into a new CampaignState.entity_fame: Dict[str, FameCarryForward] field. Implement FameImporter.get_fame(campaign_state, entity_id), a thin None-safe lookup matching CultureDriftImporter.get_culture()'s contract.
- Implement a new LegendFact class (typed durable state), explicitly named and structured to avoid collision with the pre-existing, unrelated LEGENDARY_ARRIVAL consequence-event concept (src/systems/social_systems/consequence_events.py, chronicle/significance.py's BASE_SIGNIFICANCE map) -- disambiguate explicitly in the ticket's own docs, do not conflate the two. A LegendFact is constructed/discoverable only once FameImporter.get_fame(...).fame (or the chosen axis) crosses a fame_threshold numeric constant, decided and documented during Plan phase (no existing anchor -- a real design-authority decision, same caution the atlas gives idea 34).
- Unit-test LegendFact's discoverability directly against PerceptionFilterService.filter() (src/domains/perception/filter.py) at the service level, WITHOUT wiring PerceptionUpdatePhase into any live pipeline phase and WITHOUT extending idea 34's candidate-role set. Document this honestly in Implementation Notes as "built, not yet visible in play" (matching idea 60's own precedent, TCK-20260904-REPUTATION-LOCALITY-SCOPE), not as a fully live end-to-end feature.

## Out of Scope
- Wiring PerceptionUpdatePhase into AuthoritativeApplyPipeline.refine() or any other live pipeline phase -- a separate, larger, already-disclosed gap (TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION), not this ticket's to fix.
- Wiring MotivationBiasService.compute_bias_multiplier into any live call site -- same reasoning, a separate follow-up.
- Extending idea 34's (Coming of Age) candidate-role set to include an ADVENTURER/HERO option -- idea 34's own ticket scope, not this one; this ticket only makes LegendFact perceivable/queryable, it does not modify idea 34's decision logic.
- Adding a new combat_victory/monster_slain Narrative Ledger event type -- the design doc explicitly scopes this out as "new event-scoring, not aggregation"; the resulting in-life-combat-fame gap is a disclosed, accepted limitation of Option B.
- Idea 62's Chronicle-fidelity-drift transform and idea 63's belief-institution mechanism -- sibling/downstream tickets of the same epic; per this epic's own resolution, idea 57 does NOT need idea 62's output as an input.

## Acceptance Criteria
- [x] FameDeriver.derive() on a hierarchy containing a quest_completed entry and a HERO entity_death entry for two different subject_ids produces two distinct non-zero FameState entries, each attributable to the correct subject_id, verified by a new test. (`tests/unit/domains/fame/test_fame_deriver.py::test_fame_deriver_attributes_two_subjects_distinctly`)
- [x] FameExporter.export() is called from the same episode-boundary call site as CultureDriftExporter.export(), and an untouched entity's FameCarryForward from a prior episode is preserved (not reset) when a later episode produces zero new events for them, mirroring CultureDriftExporter's own carry-forward guarantee, verified by test. (`tests/unit/domains/fame/test_fame_exporter.py::test_fame_exporter_preserves_untouched_entity_across_zero_event_episode`, `tests/unit/domains/campaigns/test_fame_wiring.py`)
- [x] A LegendFact is constructed only when FameImporter.get_fame(...)'s relevant axis crosses the Plan-phase-decided fame_threshold; a fame value below threshold produces no LegendFact, verified by test. (`tests/unit/domains/fame/test_legend_fact.py`)
- [x] LegendFact is discoverable via a direct unit-level call to PerceptionFilterService.filter(), verified by a new test, without any change to PerceptionUpdatePhase's own call-site count (still zero in the live pipeline) or to idea 34's _CANDIDATE_ROLES. (`tests/unit/domains/perception/test_legend_fact_discoverability.py`, `tests/architecture/test_fame_legend_fact_distinctness.py::test_fame_module_no_perception_update_phase_call_site_increase`, `::test_coming_of_age_candidate_roles_unchanged`)
- [x] This ticket's own LegendFact class is never confused with or merged into the pre-existing LEGENDARY_ARRIVAL concept -- verified by a source-text guard test confirming both remain distinct, separately-named classes. (`tests/architecture/test_fame_legend_fact_distinctness.py::test_fame_module_no_belief_entry_knowledge_fact_or_legendary_arrival_references`)

## Related Tickets
- TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF
- TCK-20260905-CHRONICLE-FIDELITY-DRIFT
- TCK-20260905-BELIEF-INSTITUTION-DESIGN
- TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION
- TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE

## Related Docs
- docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/rpg_expected_schemas.html
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md
- docs/simulation/domains/perception_contract.md
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None

## Related Code Areas
- src/domains/culture/deriver.py
- src/domains/culture/model.py
- src/domains/culture/exporter.py
- src/domains/campaigns/state.py
- src/domains/campaigns/orchestrator.py
- src/domains/perception/filter.py
- src/domains/perception/phase.py
- src/domains/motivation/service.py
- src/ai/coming_of_age.py
- src/systems/social_systems/consequence_events.py
- src/domains/chronicle/significance.py

## Assumptions / Open Questions
- fame_threshold's numeric value and FameState's axis count (single vs. fame+notoriety split) are both explicitly open Plan-phase decisions, not resolved by investigation.
- This ticket has no dependency on idea 62's own ticket landing first (independent sibling, per this epic's own re-confirmed resolution) -- safe to implement in either order relative to it.
- Idea 63's own ticket is hard-blocked on this ticket reaching DONE, since it must consume this ticket's actual shipped FameState/LegendFact shape.

## Implementation Notes

Implemented per staging_artifacts/TCK-20260905-FAME-DERIVER-LEGEND-FACT/plan.md's 9 steps, in
order, with no deviations from the plan's decisions (see plan.md's own Plan-Phase Decisions
section for the fame_threshold/axis-count and LegendFact-home/trigger rationale).

- **Step 1**: `src/domains/fame/model.py` — `FameState` (single `fame: float = 0.0` axis, per
  Decision 1) and `FameCarryForward` (`subject_id`, `fame`, `derived_episode`), field-for-field
  mirror of `FidelityState`/`FidelityCarryForward`.
- **Step 2**: `src/domains/fame/deriver.py` — `FameDeriver.derive(hierarchy, entity_names=None)`,
  keyed by `entry.subject_id` (falsy subject_id skipped, no `"__global__"` fallback), Option B
  event rule (`quest_completed` + HERO `entity_death`), module-local `NORMALISE_DENOMINATOR=3.0`
  independent of `CultureDeriver`'s own constant.
- **Step 3**: `src/domains/campaigns/state.py` — added `entity_fame: Dict[str, FameCarryForward]`
  field + `to_dict()`/`from_dict()` wiring, `str`-keyed (no int casting), mirroring
  `historical_drift`'s exact shape.
- **Step 4**: `src/domains/fame/exporter.py` — `FameExporter.export()` (direct dict-mutation write,
  confirmed `CampaignState` is not frozen and has no `patches.py` write path) and
  `FameImporter.get_fame()` (thin `None`-safe lookup).
- **Step 5**: Wired `FameExporter.export()` into `CampaignOrchestrator._advance_state()`
  immediately after the existing `FidelityExporter.export()` call, reusing the same `_hierarchy`
  local. This shifted `tests/architecture/test_phase18_import_boundaries.py`'s pinned
  `("src/domains/campaigns/orchestrator.py", 437)` import-line assertion down to line `440` (3
  new lines added before it) — re-pinned deliberately with a comment citing this ticket, exactly
  the collateral-drift class the sibling Fidelity ticket hit.
- **Step 6**: `src/domains/fame/legend.py` — `FAME_THRESHOLD=0.5` (anchored to
  `CHRONICLE_THRESHOLD`), `LegendFact` (frozen dataclass, plain `fame: float` snapshot, not a live
  `FameState` reference), `LegendFactService.for_entity()` (lazy, query-time construction — no new
  `CampaignState` field) and `LegendFactService.to_world_signal()` (imports only `WorldSignal`
  from `src.domains.perception.salience`, never `PerceptionUpdatePhase`/`PerceptionFilterService`
  at module level).
- **Step 7**: `tests/architecture/test_fame_legend_fact_distinctness.py` — 4 guard tests per
  plan.md, plus a 5th (`test_coming_of_age_candidate_roles_unchanged`) that plan.md's own
  Acceptance Criteria Map cited as verifying AC4 but that Step 7's own enumerated list omitted —
  added it to close that internal gap rather than leave AC4 partially unverified (see
  plan.md's Deviations section, added below).
- **Step 8**: `tests/unit/domains/perception/test_legend_fact_discoverability.py` — constructs a
  `LegendFact` via `LegendFactService.for_entity()` against a `CampaignState` seeded through
  `FameExporter.export()`, converts to a `WorldSignal`, calls
  `PerceptionFilterService.filter()` directly; asserts it lands in `perceived_opportunities`
  (existing catch-all branch, no `filter.py` change).
- **Step 9**: Docs — new §9 in `docs/mechanics/05_world_evolution.md`, new
  `docs/world/fame_legend_contract.md`, `WORLD-FAME-001`/`WORLD-FAME-002` parity ledger entries
  added via `tools/parity_ledger_writer.py::write_entry` (never hand-edited), and a "Status
  update, 2026-09-05" annotation under idea 57's own item in
  `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`.

**Honesty framing (per ticket's own AC4/Scope, matching idea 60's precedent):** this ticket is
"built, not yet visible in play." `FameImporter.get_fame()` and `LegendFactService` have no live
caller anywhere in the simulation loop — `PerceptionUpdatePhase` remains at zero live pipeline
call sites and `MotivationBiasService.compute_bias_multiplier()` remains at zero call sites
outside its own module, both confirmed unchanged by the new architecture guard. `LegendFact`
discoverability is proven only at the direct `PerceptionFilterService.filter()` service-call
level in a unit test, not through any live entity actually perceiving a legend during a
simulation run. `src/ai/coming_of_age.py`'s `_CANDIDATE_ROLES` is untouched (no `ADVENTURER`/
`HERO` bias exists to weight toward). This is a disclosed, accepted gap, not a hidden
incompleteness — the next tickets to close it (perception/motivation wiring, idea 34's own
candidate-role extension) are explicitly out of this ticket's scope.

Ran `graphify update .` (src/tests changed) and `make knowledge-index-update` (docs changed) after
implementation.

## Test Summary

All new and existing tests pass. Scoped runs executed:

- `tests/unit/domains/fame/` (new package: deriver, exporter, legend — 22 tests) — pass
- `tests/unit/domains/campaigns/test_fame_wiring.py` (new) — pass
- `tests/architecture/test_fame_legend_fact_distinctness.py` (new, 5 guards) — pass
- `tests/unit/domains/perception/test_legend_fact_discoverability.py` (new) — pass
- Full regression sweep: `tests/unit/domains/ tests/unit/strategic/test_coming_of_age_archetype_choice.py tests/unit/social/ tests/architecture/` — 1266 passed
- `tests/architecture/test_phase18_import_boundaries.py` (re-pinned line 437→440) — pass
- `tests/integration/culture/ tests/integration/campaigns/ tests/integration/scenarios/test_campaign_chronicle.py tests/integration/scenarios/test_campaign_runtime.py` — 11 passed, 5 deselected (slow-marked)
- All sibling read-only precedent suites (`test_fidelity_write_paths.py`, culture/fidelity
  deriver/exporter suites) confirmed unmodified and still passing.

## Files Changed

- `src/domains/fame/__init__.py` (new)
- `src/domains/fame/model.py` (new)
- `src/domains/fame/deriver.py` (new)
- `src/domains/fame/exporter.py` (new)
- `src/domains/fame/legend.py` (new)
- `src/domains/campaigns/state.py` (edited — `entity_fame` field + serialization wiring)
- `src/domains/campaigns/orchestrator.py` (edited — `FameExporter.export()` wired into `_advance_state()`)
- `tests/unit/domains/fame/__init__.py` (new)
- `tests/unit/domains/fame/test_fame_deriver.py` (new)
- `tests/unit/domains/fame/test_fame_exporter.py` (new)
- `tests/unit/domains/fame/test_legend_fact.py` (new)
- `tests/unit/domains/campaigns/test_fame_wiring.py` (new)
- `tests/unit/domains/perception/test_legend_fact_discoverability.py` (new)
- `tests/architecture/test_fame_legend_fact_distinctness.py` (new)
- `tests/architecture/test_phase18_import_boundaries.py` (edited — re-pinned import line 437→440)
- `docs/mechanics/05_world_evolution.md` (edited — new §9 "Living Legend Fame")
- `docs/world/fame_legend_contract.md` (new)
- `docs/parity_ledger/world_dynamics.yaml` (edited — `WORLD-FAME-001`, `WORLD-FAME-002` added via `tools/parity_ledger_writer.py`)
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` (edited — idea 57 status annotation)
- `staging_artifacts/TCK-20260905-FAME-DERIVER-LEGEND-FACT/plan.md` (edited — Deviations section added)
- `tickets/inprogress/TCK-20260905-FAME-DERIVER-LEGEND-FACT.md` (this file)

## Completion Summary

Implemented the full idea-57 Living Legend Feedback Loop aggregation shape: `FameDeriver`/
`FameState`/`FameCarryForward`/`FameExporter`/`FameImporter` (`src/domains/fame/`), structurally
mirroring the just-landed `FidelityDeriver` sibling exactly, keyed by
`NarrativeLedgerEntry.subject_id` and accumulating Option B events (`quest_completed` +
HERO `entity_death`). Wired `FameExporter.export()` into
`CampaignOrchestrator._advance_state()` alongside `CultureDriftExporter`/`FidelityExporter`,
persisting into a new `CampaignState.entity_fame` field. Added a lazy, non-durable `LegendFact`
read-model (`FAME_THRESHOLD=0.5`) constructed at query time via `LegendFactService`, with
discoverability proven directly against `PerceptionFilterService.filter()`. All 5 acceptance
criteria are met and verified by new tests; 4 architecture guards (plus a 5th closing an internal
plan.md gap) confirm the sole-writer invariant, `LegendFact`/`LEGENDARY_ARRIVAL` distinctness, and
zero dormant-system call-site increase. Docs (`docs/mechanics/05_world_evolution.md` §9,
`docs/world/fame_legend_contract.md`) and parity ledger (`WORLD-FAME-001`/`-002`) updated. This is
a "built, not yet visible in play" feature by design — no live perception/motivation consumer
exists yet, matching idea 60's own honesty precedent.
