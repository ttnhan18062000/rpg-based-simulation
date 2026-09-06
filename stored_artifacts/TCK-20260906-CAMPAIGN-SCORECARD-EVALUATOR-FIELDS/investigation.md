---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS
date: 2026-09-06
---

# Investigation: TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS

## Current Behavior
`CampaignScorecardEvaluator.evaluate()` (`src/domains/campaigns/scorecard.py:17-67`) computes exactly
7 fixed fields from `entity_arc_reports`/`forbidden_behaviors`/`route_diversity` — none touch
reputation, nemesis, or Chronicle fidelity. Confirmed unchanged since the ticket's own citation.

`CampaignScorecardEvaluator.evaluate()` is called from exactly one place in the whole codebase:
`SimulationAnalysisRunner.run()` (`src/domains/campaigns/runner.py:152`), a **single-episode**,
single-`Kernel`-run subsystem — no episodes, no Chronicle compilation, no cross-episode state.
`CampaignOrchestrator` (`src/domains/campaigns/orchestrator.py`, the real multi-episode system idea
53/55/58/62 actually live in) **never calls `CampaignScorecardEvaluator` anywhere** (0 references,
confirmed via grep). This is a real premise flaw in the M9 epic doc itself (lines 29/58 assumed these
two systems were already integrated) — confirmed independently by the orchestrating session.

## Three corrections made during this Investigate phase (disclosed, not silently applied)

**Correction 1 — decouple scorecard fields from the 4-episode test.** Since `CampaignScorecardEvaluator`
is structurally unreachable from `CampaignOrchestrator`, AC1/AC3 (new evaluator fields) and AC2 (the
4-episode test) are two independently-verified pieces of work, not one integrated pipeline. Per the
ticket's own Out-of-Scope ("Redesigning `CampaignOrchestrator`/`CampaignScorecardEvaluator`'s existing
7 fields — additive only"), wiring the evaluator into `CampaignOrchestrator` is explicitly NOT done
here — that would be a new, larger integration point nobody asked for.

**Correction 2 — no cross-episode data path exists for AC2's literal 4-episode framing.**
`EntityCarryForward` (`src/domains/campaigns/state.py:95-122`, the actual cross-episode persistence
type) has exactly 6 fields: `entity_id/level/xp/equipment/reputation/alive`. It carries **none** of
`heir_entity_id`, `strategic.blockers` (idea 55's nemesis-transfer target), or
`motivation.named_intention` (idea 58's dying wish) across episode boundaries — confirmed via
`_extract_entity_carry_forwards()` (orchestrator.py:470-495), which reads only those 6 fields off
`AuthoritativeState`. Separately, `CampaignOrchestrator.run_episode()` never exposes the completed
episode's `final_state` externally — `EpisodeSummary` (state.py:169-187) has only
`episode_index/completed_tick/run_id`. So idea 55/58's outcomes cannot be asserted in a *later*
episode as the ticket's Episode-3 framing originally assumed — they must be asserted **within the
same episode/tick** they are produced.

**Correction 3 — "inherited_reputation_seed on the heir" does not exist in real code; idea 53 and idea
55/58 are unrelated mechanisms.** `V2EntityBuilder.birth_record()` (`src/core/builder.py:625-665`)
seeds a **newborn's** `SocialComponent.public_reputation` from its two **living parents'** current
reputation via `parent_a_public_reputation`/`parent_b_public_reputation` kwargs
(`ReputationService.combine_public_reputation()`, `src/systems/social_systems/reputation.py:32-40` —
simple clamped average). It has nothing to do with a dying entity's heir. Idea 55/58's heir succession
(`LifecycleSystem._transfer_inherited_feud`/`_seed_dying_wish`,
`src/systems/lifecycle_systems/lifecycle.py:28-119`) operates on a **pre-existing** heir
(`entity.lifecycle.heir_entity_id`, resolved via `_select_default_heir` from `entity.social.bonds`)
and only ever touches `strategic.blockers` (feud, id=`inherited_nemesis_{subject}`,
`severity = deceased_severity * 0.5`) and `cognition_bundle_set.motivation.named_intention` (dying
wish, a new `NamedIntentionBundle`) — never reputation at all. The M9 ticket's own text conflated
these two independently-shipped, structurally unrelated mechanisms into an imagined "dying Hero's
reputation echoes into their heir" story with no basis in real code.

## Real mechanisms confirmed, with exact field names (for the corrected test design)

- **Idea 55 (nemesis transfer)**: `LifecycleSystem._transfer_inherited_feud()` reads
  `deceased.strategic.blockers` for keys starting `"nemesis_"` (populated pre-death by
  `NemesisRelationImporter.apply()`, `src/domains/campaigns/grief_urgency.py:92-131`, from
  `CampaignState.nemesis_relations`), and writes `heir_upd.strategic.blockers_add_or_update` with a
  new `BlockerState(id=f"inherited_nemesis_{subject}", severity=original*0.5, resolved=False)`.
- **Idea 58 (dying wish)**: `LifecycleSystem._seed_dying_wish()` writes
  `heir_upd.cognition_bundle_set.motivation.named_intention = NamedIntentionBundle(text=..., 
  source_entity_id=deceased.id, created_tick=state.tick, status="PENDING")`. Wish text references the
  same nemesis antagonist if idea 55 fired, else a generic remembrance string.
- **Death trigger**: `LifecycleSystem.resolve_lifecycle()` (lifecycle.py:137-245) marks an entity dead
  when `entity.lifecycle.age_ticks >= entity.lifecycle.max_age_ticks` (OLD_AGE) — a fully deterministic
  trigger requiring no combat/AI emergent behavior, usable to force a death on tick 1 of a hand-built
  `AuthoritativeState`, exactly matching this codebase's own established "deterministic isolated proof"
  precedent (`tests/simulation_quality/test_grade_regression.py::
  test_information_intent_execution_fires_through_kernel_tick_once`, and M7's own
  `route_new_query_isolated_calibration.py`).
- **Idea 55/62's real, genuinely-cross-episode `CampaignState` fields** (usable directly, no capture
  needed): `CampaignState.nemesis_relations: Dict[str, NemesisRelation]` (state.py:312, formed by
  `_advance_nemesis_relations()` from `social_memories` interaction history,
  `NEMESIS_EPISODE_COUNT`-episode threshold) and `CampaignState.historical_drift: Dict[str,
  FidelityCarryForward]` (state.py:317, written by `FidelityExporter.export()` at every episode
  boundary from `ChronicleGrouper.group(narrative_ledger)`). `FidelityDeriver.derive()`
  (`src/domains/fidelity/deriver.py:42-72`) computes `fidelity = max(0.0, 1.0 - era_distance * 0.2)`,
  where an Era spans `ChronicleGrouper.ERA_EPISODE_MIN = 3` episodes — an event from episode 0 needs at
  least 4 real episodes to run (so a second Era begins) before `era_distance >= 1` and its fidelity
  drops below 1.0. This conveniently keeps a real "4-episode Campaign" framing for this one piece.
- **Idea 53 (reputation inheritance)**: `ReputationService.combine_public_reputation(parent_a, parent_b)`
  is a pure static function — `max(0.0, min(2.0, (a+b)/2.0))`. Testing it with two already-drifted
  values (not both 1.0 defaults) directly demonstrates the "genuinely new" claim the M9 ticket wants:
  this works with campaign-drifted reputations, not just fixture defaults.

## Docs Requiring Update
- `docs/simulation_quality/current_state.md` or `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`: note the corrected scope (evaluator fields decoupled from the 4-episode test; the 3 corrections above).
- `docs/parity_ledger/social_narrative.yaml`: new entry for the 2 new `CampaignScorecard` fields (behavior_changed=true, new production code in scorecard.py).

## Parity Ledger Overlap
- SOC-269/SOC-273/STRAT-270 (from `TCK-20260904-LINEAGE-DEATH-DISPATCH`/`TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE`) document the underlying mechanisms this ticket adds *test coverage* for — no change to their own status, since this ticket does not modify `LifecycleSystem`/`ReputationService`/`FidelityExporter` at all, only `CampaignScorecardEvaluator` (new fields) and adds tests.
- New parity entry needed for `CampaignScorecard`'s 2 new fields themselves (SOC subsystem, since they're social/narrative scorecard signals).

## Prior Work
- `tests/unit/domains/campaigns/test_phase9_semantic_campaign_scorecard.py` — existing scorecard test file, the natural home for the new field's unit tests (matches the existing 7-field pattern exactly).
- `tests/integration/scenarios/test_campaign_runtime.py` — real, `@pytest.mark.slow`-tagged, genuine Kernel-driven multi-episode `CampaignOrchestrator` infrastructure (uses real `frontier_living_world`) — the real template for the nemesis-relations/Chronicle-fidelity piece. (The ticket's own cited function name, `test_hero_pursues_craft_upgrade_across_three_episodes`, is wrong — that function actually lives in `tests/integration/campaigns/test_progression_planner_three_episode.py` and is fully `MagicMock()`-based with no real Kernel content at all; not used as a template.)
- `tests/simulation_quality/test_grade_regression.py::test_information_intent_execution_fires_through_kernel_tick_once` — the real precedent for a deterministic, hand-built, one-`Kernel.tick_once()` proof, used as the template for the nemesis-transfer/dying-wish piece.

## Risks and Open Questions
None outstanding — all 3 corrections above were confirmed jointly with the orchestrating session before this Plan was written.

## Anti-Drift Hazards
- Do not wire `CampaignScorecardEvaluator` into `CampaignOrchestrator` — explicitly out of scope, would be a much larger architectural change.
- Do not extend `EntityCarryForward` with new fields to "fix" the cross-episode gap found in Correction 2 — that gap is itself a disclosed finding of this ticket, not something to silently patch.
- Do not assert idea 58's `dying_wish_intention` in a later episode than the one it was seeded in — the architecture genuinely does not support that; assert same-episode only.
