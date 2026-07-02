---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS
phase: open
date: 2026-07-01
tags: [simq, event-emission, information, cognition, scoring]
---

# TCK-20260701-SIMQ-EMIT-LEAD-BELIEFS

## Title
SimQ: Emit INFORMATION and COGNITION deep-signal events from engine

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
INFORMATION and COGNITION are both stuck at C across all calibration runs despite full
scoring infrastructure. The first emit pass (TCK-20260629-SIMQ-EMIT-COGNITION) added
`belief_assimilated`, `belief_updated`, `lead_certainty_changed`, `self_model_updated`,
and `paid_information_transaction` — these events fire but at near-zero frequency in
200-tick runs, leaving both pillars at C.

The deeper signal gaps (from `docs/simulation_quality/event_type_coverage.md §3.2–§3.3`)
require new tracking in the strategic cognition and lead-management subsystems:

INFORMATION gaps (§3.3):
- `lead_certainty_updated` — DISTINCT from `lead_certainty_changed` (CognitionScorer).
  This is the post-processed knowledge update (InformationScorer); engine only emits
  the raw state diff, not the interpreted update.
- `lead_contradiction_resolved` — `lead_contradiction.py` emits `belief_contradiction`,
  not the resolution event.
- `paid_info_changed_goal` — no emitter: fires when an information purchase causes the
  entity to switch its active strategic goal.
- `belief_stale` — no emitter: fires when a belief's `last_updated_tick` exceeds
  configured staleness threshold.
- `decision_diverged_by_belief` — no emitter: fires when entity's decision diverges from
  expected path specifically because of a stale/wrong belief.

COGNITION gap (§3.2):
- `decision_divergence_detected` — no emitter: fires when entity makes a decision
  inconsistent with its stated goal hierarchy (potential goal-coherence diagnostic).

## Scope
1. Investigate `src/engine/pipeline_phases/lead_contradiction.py` — understand where
   contradiction resolution occurs; add `lead_contradiction_resolved` emit after resolution
2. Add `lead_certainty_updated` emitter in the InformationScorer path: this fires after the
   hub receives `lead_certainty_changed` and the knowledge update is processed — OR add a
   second emit in `event_extractor.py` when certainty crosses a meaningful threshold
   (distinction from raw diff: only emit when certainty crosses 0.25 / 0.5 / 0.75 bands)
3. Add `belief_stale` emitter: detect in `event_extractor.py` via
   `lead.last_updated_tick` age > threshold (configurable in `detection_params.yaml`);
   emit once per lead per staleness epoch, not every tick
4. Add `paid_info_changed_goal` emitter: detect when an information purchase (src_kind=INFORMATION_PURCHASE)
   correlates with a `StrategicObjectiveChanged` event on the same entity in the same tick
5. Add `decision_diverged_by_belief` emitter: detect when entity's chosen project is not
   the highest-scoring candidate AND a stale belief is on record (requires cross-referencing
   goal-score trace with belief state — complex; may be simplified to "entity chose non-top
   project while holding a belief with certainty < 0.3")
6. Add `decision_divergence_detected` (COGNITION) emitter: fires when entity's active project
   type is inconsistent with its current top-level strategic objective tier
   (e.g., pursuing ECONOMY project while objective tier is SURVIVAL)
7. Update `docs/simulation_quality/event_type_coverage.md §3.2–§3.3`
8. Add unit tests for each new emitter

## Out of Scope
- Modifying InformationScorer or CognitionScorer scoring weights
- Changing lead management architecture
- Implementing new cognitive systems

## Acceptance Criteria
- [ ] All 6 event types emitted under correct conditions (5 INFORMATION + 1 COGNITION)
- [ ] Each event reaches the correct scorer (verify via unit tests)
- [ ] `event_type_coverage.md §3.2–§3.3` updated — 6 entries removed
- [ ] Staleness threshold for `belief_stale` recorded in `config/simulation_quality/detection_params.yaml`
- [ ] No regression in existing cognition / strategic tests

## Related Tickets
- TCK-20260629-SIMQ-EMIT-COGNITION — prior emit pass (belief/certainty events)
- TCK-20260627-P1H-GOAL-RUNNERUP — runner-up scores in trace (decision divergence reference)
- TCK-20260627-P1B-QUEST-ACTIVATION — lead contradiction resolution (context)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.2–§3.3`
- `docs/simulation_quality/quality_scoring_contract.md §5` — InformationScorer, CognitionScorer contracts
- `docs/mechanics/04_strategic_cognition.md` — lead certainty and knowledge management laws

## Related Code Areas
- `src/engine/pipeline_phases/lead_contradiction.py` — contradiction resolution
- `src/observability/event_extractor.py` — where state-diff emitters live
- `src/domains/intelligence/` or `src/systems/strategic_systems/intelligence.py` — strategic goal tracking
- `src/simulation_quality/scorers/information_scorer.py`, `cognition_scorer.py`
- `config/simulation_quality/detection_params.yaml` — threshold configuration

## Assumptions / Open Questions
- `decision_divergence_detected` and `decision_diverged_by_belief` overlap conceptually —
  investigate whether they can share an emitter or require separate signal paths.
- `paid_info_changed_goal` requires correlating two events in the same tick; confirm the
  event_extractor processes intents before strategic updates in the pipeline phase order.

## Test Summary
- Unit: `belief_stale` fires after configurable staleness window, not before
- Unit: `lead_certainty_updated` fires only on band crossing (0.25/0.5/0.75), not on every diff
- Unit: `decision_divergence_detected` fires when project type mismatches objective tier
- Integration: 500-tick run with strategic-heavy world shows > 0 INFORMATION events beyond
  the baseline `belief_assimilated` / `lead_certainty_changed`

## Files Changed
- `src/observability/event_extractor.py` — 6 new emitters + class-level tracking dicts + reset_run_state()
- `src/engine/pipeline_phases/lead_contradiction.py` — added lead_contradiction_resolved emit
- `config/simulation_quality/detection_params.yaml` — belief_stale_threshold: 50
- `tests/unit/observability/test_event_extractor_information2.py` — 14 new unit tests
- `tests/unit/cognition/test_information_seeking.py` — updated 2 assertions for lead_contradiction_resolved
- `docs/parity_ledger/strategic_cognition.yaml` — updated STRAT-230; added STRAT-240, STRAT-241, STRAT-242
- `docs/simulation_quality/event_type_coverage.md` — §3.2, §3.3 gaps marked resolved

## Completion Summary
All 6 emitters implemented in event_extractor.py (lead_certainty_updated, belief_stale,
paid_info_changed_goal, decision_diverged_by_belief, decision_divergence_detected) and
lead_contradiction_resolved added to lead_contradiction.py. 14 unit tests pass; 723 total
observability+cognition tests pass. Parity ledger updated with STRAT-240–242. Coverage
doc updated for §3.2–§3.3. Staleness threshold in detection_params.yaml.
