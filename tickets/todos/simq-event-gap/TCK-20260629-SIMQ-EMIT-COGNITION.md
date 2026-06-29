---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-COGNITION
phase: open
date: 2026-06-29
tags: [simq, observability, event-gap, cognition, belief]
---

# TCK-20260629-SIMQ-EMIT-COGNITION

## Title
SimQ: Emit COGNITION and INFORMATION Pillar Events from Belief and Lead Phases

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The COGNITION pillar scores 6 event types and the INFORMATION pillar scores 7 event types.
The engine currently emits `StrategicProjectChanged`, `StrategicObjectiveChanged`, and
`StrategicConcernRaised` from the cognition recorder, but these only partially cover the
contract vocabulary. Missing: `belief_updated`, `lead_certainty_changed`,
`self_model_updated`, `decision_divergence_detected`, `knowledge_default_fallback`,
`belief_assimilated`, `lead_certainty_updated`, `lead_contradiction_resolved`,
`paid_information_transaction`, `paid_info_changed_goal`, `belief_stale`,
`decision_diverged_by_belief`.

These require hooks in PP-03 (self_model), PP-04 (information_belief), PP-26
(paid_information), and PP-30 (strategic_intelligence).

## Scope
Add `EventRecorder.record()` calls at belief assimilation, lead scoring, and paid
information phase execution sites.

**COGNITION events to emit:**

| Event type | Source phase | Trigger |
|---|---|---|
| `belief_updated` | PP-04 | When entity's known state changes from new information |
| `lead_certainty_changed` | PP-30 | When lead certainty score increases or decreases |
| `self_model_updated` | PP-03 | When entity's self-model is refreshed with new vital state |
| `decision_divergence_detected` | PP-30 | When two entities in same region choose different routes due to belief difference |
| `knowledge_default_fallback` | PP-12/PP-30 | When entity makes decision on zero knowledge (no leads with certainty > 0) |

**INFORMATION events to emit:**

| Event type | Source phase | Trigger |
|---|---|---|
| `belief_assimilated` | PP-04 | Belief successfully integrated (distinct from belief_updated — this is the outcome event) |
| `lead_certainty_updated` | PP-30 | Lead certainty score updated from scoring pass |
| `lead_contradiction_resolved` | PP-30 | Conflicting lead certainties reconciled |
| `paid_information_transaction` | PP-26 | Entity pays gold for information tip |
| `paid_info_changed_goal` | PP-26 + PP-12 | Paid info transaction followed by strategic goal change within 5 ticks |
| `belief_stale` | PP-04 | Belief certainty decayed below threshold on active information |
| `decision_diverged_by_belief` | PP-30 | Same trigger as `decision_divergence_detected` (emit once, both scorers handle it) |

Note: `decision_diverged_by_belief` and `decision_divergence_detected` are the same event;
emit as `decision_diverged_by_belief` — the translation layer (TCK-20260629-SIMQ-EVENT-TRANSLATE)
should remap `decision_diverged_by_belief` → `decision_divergence_detected` for COGNITION scorer.

**Architecture constraint:** No import of `src/simulation_quality/` from engine phases.

## Out of Scope
- `paid_info_changed_goal` requires cross-tick correlation — implement via a stateful
  tracker in PP-26 that notes recent paid transactions and checks goal in subsequent ticks.
  If this is too complex, document as a known gap and emit only when same-tick goal change
  is detected.
- AGENCY events: TCK-20260629-SIMQ-EMIT-AGENCY

## Acceptance Criteria
- [ ] `belief_updated` emitted from PP-04 when entity known state changes
- [ ] `lead_certainty_changed` emitted from PP-30 with `{"lead_id", "delta", "new_certainty"}`
- [ ] `self_model_updated` emitted from PP-03 when self-model refresh occurs
- [ ] `paid_information_transaction` emitted from PP-26 with `{"gold_cost", "info_type"}`
- [ ] `belief_assimilated` emitted from PP-04 on successful integration
- [ ] `lead_certainty_updated` emitted from PP-30 on each lead scoring pass
- [ ] `decision_diverged_by_belief` emitted when two entities in same region diverge routes
- [ ] No import of `src/simulation_quality/` from PP-03/04/26/30
- [ ] Unit tests mock phases and assert events recorded
- [ ] COGNITION and INFORMATION pillars show non-zero events in calibration run

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite)
- TCK-20260629-SIMQ-EMIT-AGENCY (sibling — agency phase hooks)
- SIMQ-CALIBRATED-001 parity entry

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COGNITION, INFORMATION
- `docs/mechanics/04_strategic_cognition.md` — belief and lead system laws

## Related Code Areas
- PP-03 (self_model), PP-04 (information_belief), PP-26 (paid_information), PP-30 (strategic_intelligence)
- `src/observability/cognition/events.py` — existing StrategicCognitionEvent subclasses

## Assumptions / Open Questions
- PP-04 `information_belief` phase has a discrete "belief assimilated" outcome vs "no change"
  that can be detected at call site
- PP-30 lead scoring produces a certainty delta value per lead per entity
- `paid_information_transaction` gold cost is visible at PP-26 dispatch site
- `decision_divergence_detected` requires comparing route decisions of multiple entities in
  same region — may need a post-phase aggregation step rather than per-entity hook
