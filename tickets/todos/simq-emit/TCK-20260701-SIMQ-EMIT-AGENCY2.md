---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-AGENCY2
phase: open
date: 2026-07-01
tags: [simq, event-emission, agency, scoring]
---

# TCK-20260701-SIMQ-EMIT-AGENCY2

## Title
SimQ: Emit AGENCY pillar tracking events (defer, abandon, cascade, novelty)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The AGENCY pillar scores B when `ENABLE_ADVENTURE_ROUTING=ON` (simq_routing_test confirms
this) and C otherwise. The first AGENCY emit pass (TCK-20260629-SIMQ-EMIT-AGENCY) added
`route_selected` and `action_executed`. The remaining 4 gaps (§3.1) capture decision-quality
signals: deferral reasons, abandonment events, cascade detection, and novel route use — these
would give AGENCY richer signal even in non-routing runs.

Missing events (from §3.1):
- `defer_with_reason` — defined in `src/domains/adventure/schema.py` as DEFER_WITH_REASON;
  currently embedded in `route_selected` payload.family field rather than a separate event
- `commitment_abandoned` — no emitter found; entity abandons a committed course of action
- `rejection_cascade_tick` — no emitter found; per-tick aggregate when N projects rejected in one tick
- `route_family_first_use` — no emitter found; fires once per novel routing family per entity

## Scope
1. Add `defer_with_reason` emitter: in the adventure routing phase, when `payload.family ==
   DEFER_WITH_REASON`, emit a separate `defer_with_reason` event alongside (or instead of
   embedding in `route_selected`). Payload: `entity_id`, `reason`, `tick`, `deferred_goal`
2. Add `commitment_abandoned` emitter: detect in `AbandonmentEvaluator` path
   (see TCK-20260627-P1F-ABANDONMENT-TYPE — AbandonmentClassification is now typed).
   Emit when `AbandonmentClassification.category != SURVIVAL` (greedy or voluntary).
   Payload: `entity_id`, `project_id`, `category`, `penalty`
3. Add `rejection_cascade_tick` emitter: in `StrategicIntelligenceSystem` or
   `evaluate_strategic_intent`, count consecutive rejections per tick; emit once per tick
   when count exceeds threshold (use same threshold as P1-A: `_MAX_CONSECUTIVE_REJECTIONS=20`).
   Payload: `entity_id`, `rejection_count`, `tick`, `dominant_failure_reason`
4. Add `route_family_first_use` emitter: track `seen_routing_families: set[str]` per entity
   in a lightweight transient registry; emit when `route_selected.family` not in seen set,
   then add to set. Payload: `entity_id`, `family`, `tick`
   Note: `seen_routing_families` is a per-run diagnostic, not durable state — store in
   a separate non-AuthoritativeState dict in the emitter module
5. Update `docs/simulation_quality/event_type_coverage.md §3.1`
6. Add unit tests

## Out of Scope
- Changing AgencyScorer weights
- Modifying routing decision logic
- Making `seen_routing_families` durable across ticks (violates durable state rules for
  non-meaningful state)

## Acceptance Criteria
- [ ] All 4 event types emitted under correct conditions
- [ ] `commitment_abandoned` payload uses `AbandonmentClassification` fields (typed)
- [ ] `rejection_cascade_tick` fires at most once per entity per tick
- [ ] `route_family_first_use` fires exactly once per novel family per entity per run
- [ ] `event_type_coverage.md §3.1` updated — 4 entries removed
- [ ] No regression in existing agency / routing tests

## Related Tickets
- TCK-20260629-SIMQ-EMIT-AGENCY — prior agency emit pass (route_selected, action_executed)
- TCK-20260627-P1A-REJECTION-BACKOFF — rejection cascade context and threshold (P1-A fix)
- TCK-20260627-P1F-ABANDONMENT-TYPE — AbandonmentClassification typed return (commitment_abandoned reference)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.1`
- `docs/simulation_quality/quality_scoring_contract.md §5` — AgencyScorer contract
- `docs/mechanics/04_strategic_cognition.md` — goal interruption and commitment rules

## Related Code Areas
- `src/domains/adventure/schema.py` — DEFER_WITH_REASON definition
- `src/domains/adventure/phase.py` — routing phase execution
- `src/domains/commitment/abandonment.py` — AbandonmentEvaluator
- `src/systems/strategic_systems/intelligence.py` — rejection tracking
- `src/simulation_quality/scorers/agency_scorer.py`

## Assumptions / Open Questions
- `route_family_first_use` uses a transient per-run registry. Confirm this doesn't need
  to survive tick boundaries for correctness (it doesn't — "first use in this run" is the signal).
- `defer_with_reason` may already be partially in `route_selected` payload — decide whether
  to add a separate event or just ensure the `family == DEFER_WITH_REASON` case produces a
  translated `defer_with_reason` event via `_TRANSLATE_CONDITIONAL`.

## Test Summary
- Unit: `route_family_first_use` fires once on first use, not on subsequent uses of same family
- Unit: `rejection_cascade_tick` fires when entity exceeds threshold, not below it
- Unit: `commitment_abandoned` payload `category` matches AbandonmentClassification
- Integration: 500-tick dungeon_crawl run shows at least 1 `defer_with_reason` event

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
