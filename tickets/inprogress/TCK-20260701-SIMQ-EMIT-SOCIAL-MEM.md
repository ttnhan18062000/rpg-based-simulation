---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-SOCIAL-MEM
phase: open
date: 2026-07-01
tags: [simq, event-emission, social, scoring, infrastructure]
---

# TCK-20260701-SIMQ-EMIT-SOCIAL-MEM

## Title
Wire social_memory_created emitter: add event recorder to SocialMemoryExporter

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`social_memory_created` is a SocialScorer event type (+2 `relationship_depth` signal).

**Premise correction (2026-07-01):** The original scope assumed emitting from
`SocialMemoryExporter.export()`. This was wrong — `SocialMemoryExporter` is campaign-layer
only (pure static method called at episode end by `CampaignOrchestrator`). It is not
reachable during normal simulation ticks.

Correct approach: emit from `EventExtractor` when `entity.social.trust_history` gains a
new significant entry. This requires no infrastructure changes — only a new emitter block
in `event_extractor.py`, exactly like `cooperation_event` and `reputation_delta`.

## Scope
1. In `EventExtractor.extract()`, for each entity update, diff `entity.social.trust_history`
   between prior and current state. For each new `other_entity_id` key added (or existing
   key that crosses ±0.3 threshold), emit:
   ```python
   SimulationEvent(
       event_type="social_memory_created",
       event_category="social",
       entity_id=entity.id,
       payload={"other_entity_id": other_id, "score": new_score},
   )
   ```
2. Gate: only emit once per (entity_id, other_entity_id) pair per run to avoid per-tick
   spam (use a `_emitted_social_memory: set[tuple[int,int]]` class-level set, reset in
   `reset_run_state()`).
3. Add unit tests: trust_history gains new entry → event emitted; existing entry updated
   below threshold → no event; second tick same pair → no duplicate.
4. Update `event_type_coverage.md §3.8` — move `social_memory_created` to §1.1.

## Out of Scope
- Changing the SocialMemoryRecord schema
- Modifying SocialScorer weights

## Acceptance Criteria
- [ ] `social_memory_created` emitted from `EventExtractor` when `trust_history` gains a significant new entry
- [ ] Emitted at most once per (entity_id, other_entity_id) pair per run
- [ ] Event reaches SocialScorer (verified via unit test)
- [ ] No regression in existing social/cooperation tests
- [ ] `event_type_coverage.md §3.8` updated — `social_memory_created` moved to §1.1

## Related Tickets
- TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY — identified the block
- TCK-20260628-SIMQ-EPIC — parent epic

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.8`
- `docs/simulation_quality/quality_scoring_contract.md §5 SOCIAL`

## Related Code Areas
- `src/domains/social/` or `src/systems/social/` — SocialMemoryExporter
- `src/observability/event_recorder.py` — EventRecorder interface

## Assumptions / Open Questions
- Threshold for "significant" trust_history entry: new key added OR existing key delta ≥ 0.3.
  Can be tightened at calibration time.
- `trust_history` is `Dict[int, float]` on `entity.social` (confirmed from `social_memory.py`
  and `SocialMemoryImporter.apply()`).
- Once-per-run gate prevents spam; if per-episode granularity is later wanted, gate should
  use `(entity_id, other_entity_id, episode)` instead.

## Test Summary
- Unit: trust_history gains new entry → `social_memory_created` event emitted
- Unit: second tick same pair → no duplicate (once-per-run gate)
- Unit: delta below threshold → no event
- Unit: payload contains `other_entity_id` and `score`

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
