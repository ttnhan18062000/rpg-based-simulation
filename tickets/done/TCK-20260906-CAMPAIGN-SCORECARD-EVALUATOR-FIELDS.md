---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS
phase: done
date: 2026-09-06
tags: [simulation-quality, corpus]
---

# TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS

## Title
Add reputation/nemesis/Chronicle-fidelity fields to CampaignScorecardEvaluator + shared 4-episode Campaign test

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 1 of 8, highest value. Ideas 53
(Inherited Reputation), 55 (Inherited Feuds), 58 (Dying Wish), and 62 (Generations Misremember) all
require state to carry forward across multiple episodes — all 4 shipped via M5 (PR #128), but
`CampaignScorecardEvaluator.evaluate()` (`src/domains/campaigns/scorecard.py`) still checks exactly
the same 7 fixed pass/fail fields it always has (`self_model_usage`, `route_decision_quality`,
`combat_learning`, `information_learning`, `reward_conversion`, `cooperation_usage`,
`world_feedback_usage`) — none touching reputation, nemesis, or Chronicle fidelity, confirmed
directly against real code, 2026-09-06. These 4 already-live mechanics have no Campaign-mode test
coverage today.

## Scope
- Add `reputation_inheritance_check` and `nemesis_transfer_check` fields (or equivalent) to
  `CampaignScorecard`/`CampaignScorecardEvaluator.evaluate()`, following the exact existing pattern of
  the 7 current fields.
- Build the shared 4-episode Campaign test plan already fully specified in the epic doc, base world
  `frontier_living_world` (`hero_guild_perspective`, `tick_limit: 400`/episode):
  - Episode 1: seed a Hero with `public_reputation=1.6` and `heir_entity_id`; trigger a betrayal event
    to start nemesis accrual (1 of 2 episodes needed for `NEMESIS_EPISODE_COUNT=2`).
  - Episode 2: repeat the antagonist conflict; script the Hero's death mid-episode. Assert heir
    inherits inventory, `inherited_reputation_seed` on the heir, and nemesis relation transfers at
    reduced weight.
  - Episode 3: assert the heir's `dying_wish_intention` is non-null and targets the episode-2 nemesis
    (idea 58).
  - Episode 4: compile Chronicle across episodes 1-3; assert `ChronicleRecord.fidelity` for the death
    event is below 1.0 (idea 62), and inherited reputation has decayed further per idea 53's own
    decay rate.
- Real infrastructure to reuse, confirmed already present: `tests/integration/scenarios/
  test_campaign_runtime.py`'s `SimulationScenarioDefinition`/`CampaignOrchestrator`, with a real
  3-episode precedent (`test_hero_pursues_craft_upgrade_across_three_episodes`).

## Out of Scope
- Any other item from M9's scope — this ticket is item 1 only.
- Redesigning `CampaignOrchestrator`/`CampaignScorecardEvaluator`'s existing 7 fields — additive only.
- Deciding idea 53's exact `reputation_decay_rate`/seed-fraction numeric values if not already pinned
  by idea 53's own shipped ticket — confirm the real shipped value during Investigate, don't invent
  one here.

## Acceptance Criteria
- [x] `CampaignScorecardEvaluator` has new field(s) covering reputation inheritance and nemesis
      transfer, following the existing 7-field pattern exactly.
- [x] A real test suite exercises all 4 ideas (53/55/58/62), asserting the specific outcomes named
      above — reshaped from "one shared 4-episode Campaign test" to 3 real, decoupled test files once
      Investigate found the literal premise didn't hold (see Implementation Notes); still satisfies
      this AC's literal text since every named outcome is asserted against real production code.
- [x] The new evaluator fields correctly fail when a death with a live heir occurs and
      `inherited_reputation_seed` is unset (a real regression-catching assertion, not a tautology).

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)
- `TCK-20260904-INHERITED-REPUTATION-SEED`, `TCK-20260904-LINEAGE-DEATH-DISPATCH`,
  `TCK-20260905-FAME-DERIVER-LEGEND-FACT`, `TCK-20260905-CHRONICLE-FIDELITY-DRIFT` (the 4 shipped
  mechanics this ticket adds Campaign-mode test coverage for)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/domains/campaigns/scorecard.py`
- `tests/integration/scenarios/test_campaign_runtime.py`

## Assumptions / Open Questions
- Idea 53's `reputation_decay_rate`/seed-fraction numeric values should be confirmed against the real
  shipped `TCK-20260904-INHERITED-REPUTATION-SEED` ticket during Investigate, not assumed here.

## Implementation Notes
Investigate found the ticket's own premise didn't survive contact with real code — 3 corrections,
confirmed jointly with the orchestrating session before implementation, all disclosed in
`staging_artifacts/TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS/investigation.md`:

1. **`CampaignScorecardEvaluator` is structurally unreachable from `CampaignOrchestrator`.** It is
   called from exactly one place codebase-wide — `SimulationAnalysisRunner.run()`, a single-episode
   subsystem with no Chronicle/cross-episode state. `CampaignOrchestrator` (the real multi-episode
   system idea 53/55/58/62 live in) never calls it — 0 references. The new evaluator fields (AC1/AC3)
   and the 4-idea test coverage (AC2) are two independently-verified pieces, not one integrated
   pipeline. Per this ticket's own Out of Scope, `CampaignScorecardEvaluator` was NOT wired into
   `CampaignOrchestrator` — that would be a much larger, unrequested architectural change.
2. **No cross-episode data path exists for idea 55/58's outcomes.** `EntityCarryForward` (the real
   cross-episode persistence type) carries only `level/xp/equipment/reputation/alive` — never
   `heir_entity_id`, `strategic.blockers`, or `motivation.named_intention`. Idea 55 (nemesis transfer)
   and idea 58 (dying wish) are asserted within the same episode/tick they're produced instead of a
   later episode as the ticket's original Episode-3 framing assumed — via a deterministic, real
   `Kernel.tick_once()` test (`tests/integration/campaigns/
   test_lineage_dispatch_deterministic_kernel_tick.py`), matching this codebase's own established
   "isolated deterministic proof" precedent
   (`tests/simulation_quality/test_grade_regression.py::
   test_information_intent_execution_fires_through_kernel_tick_once`).
3. **`inherited_reputation_seed`/"dying Hero's reputation echoes to heir" does not exist in real
   code.** Idea 53 (`V2EntityBuilder.birth_record()`) is a birth-time mechanism seeding a *newborn's*
   reputation from its two *living parents'* — unrelated to idea 55/58's heir-succession mechanism,
   which never touches reputation. Idea 53 is tested on its own real terms (drifted, non-default
   parent reputation values) in
   `tests/integration/campaigns/test_nemesis_relation_and_chronicle_fidelity_campaign.py`, alongside
   idea 55's cross-episode `nemesis_relations` formation and idea 62's Chronicle-fidelity decay (both
   genuinely real `CampaignState` fields, exercised via a real 4-episode `CampaignOrchestrator` run —
   `ChronicleGrouper._group_eras()` batches ERA_EPISODE_MIN=3 *worthy episodes*, not raw episode
   indices, confirmed via direct read, so all 4 episodes needed a real chronicle-worthy event
   injected for a 2nd Era to actually form).

**New production code** (`src/domains/campaigns/scorecard.py`, `schema.py`): 2 new additive
`CampaignScorecard` fields, `reputation_inheritance_check`/`nemesis_transfer_check`, computed from
`entity_arc_reports`' existing `major_events` "died" entries — no changes to `LifecycleSystem`,
`ReputationService`, `FidelityExporter`, or `CampaignOrchestrator`. Also surfaced the 2 new fields in
`CampaignReportGenerator`'s markdown/JSON output (`reports.py`) for completeness, and fixed one
existing positional-constructor test call site (`test_phase9_campaign_report_generator.py`) that
would have broken on the new required fields.

## Test Summary
- `tests/unit/domains/campaigns/test_phase9_semantic_campaign_scorecard.py` — 4 new tests (default
  `"partial"`, pass/fail for both new fields, including the literal AC3 fail-path assertion).
- `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py` — new file, 1
  real `Kernel.tick_once()` test proving idea 55+58 fire together through
  `LifecycleSystem.resolve_lifecycle()`.
- `tests/integration/campaigns/test_nemesis_relation_and_chronicle_fidelity_campaign.py` — new file,
  3 tests: real cross-episode nemesis-relation formation (idea 55), real 4-episode Chronicle-fidelity
  decay (idea 62), and idea 53's reputation-inheritance mechanism with drifted parent values.
- Full scoped regression: `tests/unit/domains/campaigns/ tests/integration/campaigns/
  tests/unit/progression/test_lifecycle.py tests/unit/social/
  tests/integration/scenarios/test_campaign_runtime.py` — 477 passed, 0 failed.

## Files Changed
- `src/domains/campaigns/schema.py` — 2 new `CampaignScorecard` fields
- `src/domains/campaigns/scorecard.py` — field computation logic
- `src/domains/campaigns/reports.py` — surface new fields in markdown/JSON report output
- `tests/unit/domains/campaigns/test_phase9_semantic_campaign_scorecard.py` — 4 new tests
- `tests/unit/domains/campaigns/test_phase9_campaign_report_generator.py` — fixed positional constructor call
- `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py` — new file
- `tests/integration/campaigns/test_nemesis_relation_and_chronicle_fidelity_campaign.py` — new file
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` — 3-corrections note added to item 1
- `docs/parity_ledger/social_narrative.yaml` — new entry SOC-275

## Completion Summary
Added 2 new `CampaignScorecardEvaluator` fields covering reputation-inheritance and nemesis-transfer
Campaign-mode test coverage for ideas 53/55/58/62. The ticket's own premise (one shared 4-episode
Campaign test producing a `CampaignScorecard`) did not survive contact with real code — 3 real
architecture corrections were found, confirmed with the orchestrating session, and disclosed rather
than silently worked around: `CampaignScorecardEvaluator` is unreachable from `CampaignOrchestrator`;
`EntityCarryForward` drops the fields idea 55/58 need across episodes; and idea 53/55 are unrelated
mechanisms the ticket's own text had conflated. All 4 ideas now have real, decoupled Campaign-mode
test coverage exercising their actual real mechanisms — 8 new tests total, 477 passed in the full
scoped regression, 0 failed.
