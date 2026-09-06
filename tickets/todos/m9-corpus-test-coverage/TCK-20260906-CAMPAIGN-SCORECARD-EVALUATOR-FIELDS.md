---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS
phase: open
date: 2026-09-06
tags: [simulation-quality, corpus]
---

# TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS

## Title
Add reputation/nemesis/Chronicle-fidelity fields to CampaignScorecardEvaluator + shared 4-episode Campaign test

## Status
OPEN

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
- [ ] `CampaignScorecardEvaluator` has new field(s) covering reputation inheritance and nemesis
      transfer, following the existing 7-field pattern exactly.
- [ ] The shared 4-episode Campaign test runs end-to-end and exercises all 4 ideas (53/55/58/62) in
      one Campaign, asserting the specific outcomes named above.
- [ ] The new evaluator fields correctly fail when a death with a live heir occurs and
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

## Test Summary

## Files Changed

## Completion Summary
