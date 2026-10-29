---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-QUALITY-HUB-WRITES-A-SCORE-LINE-FOR-A-REDELIVERED-EVENT
phase: done
date: 2026-10-28
tags: []
---

# TCK-20261028-QUALITY-HUB-WRITES-A-SCORE-LINE-FOR-A-REDELIVERED-EVENT

## Title
QualityHub persists a score record before the accumulator's event_id dedupe, so a redelivered event writes a duplicate quality_scores line

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`QualityHub.on_envelope` calls `self._accumulators[pillar].add(record)` and then `self._persistence.write(record)` unconditionally (src/simulation_quality/quality_hub.py:172-174). The dedupe on `event_id` lives only inside `PillarAccumulator.add` (pillar_accumulator.py:44-46), so a redelivered envelope (broker mode: stream redelivery or XCLAIM) is not counted twice but is written twice to quality_scores.jsonl. Side note: `QualityHub.update_entity_count` (quality_hub.py:209) has no caller, so `_entity_count` is always 0; no scorer reads it.

## Scope
- Make persistence follow the same dedupe as the accumulator: write only a record the accumulator accepted (for example `add()` returns whether it was new). The fix must apply to every write path in the hub.
- Side note: either delete `update_entity_count` / `_entity_count` as dead code, or leave them and state why. Decide in the plan, without wiring a new caller.

## Out of Scope
- Broker or stream delivery semantics themselves.

## Acceptance Criteria
- Feeding the same envelope twice writes one line and counts once. A test pins both.
- The pillar scores of a normal (non-redelivered) run are unchanged.

## Related Tickets
## Related Docs
- docs/observability/decision_trace_contract.md, docs/guides/observability.md (check whether either names the field)
## Related Stored Artifacts
## Related Code Areas
- src/simulation_quality/quality_hub.py
- src/simulation_quality/pillar_accumulator.py
## Assumptions / Open Questions
- Reported by lead-planner-u24 on 2026-10-28 from java-training-7a's questions, and checked by rpg-planner against origin/main (ea755bf43). It does not affect simulation results. Not dispatched yet.
- The accumulator dedupe is per pillar. Can one event legitimately score into two pillars? If so, the write rule is per (event_id, pillar), not per event_id.
## Implementation Notes
PillarAccumulator.add returns True when new; QualityHub writes the score line only then (single write path). Per pillar: one event can score into two pillars (near_death_survival: CombatScorer and ProgressionScorer), each accumulator dedupes on its own, so the rule is per (event_id, pillar): one line per pillar, each once. _entity_count/update_entity_count left in place: _entity_count feeds the scoring context at :186, is always 0, no scorer reads it (rpg-planner: do not delete in this batch).
## Test Summary
Redelivered envelope: one count, one write (pinned). tests/simulation_quality: all passed in the 583.
## Files Changed
src/simulation_quality/pillar_accumulator.py, src/simulation_quality/quality_hub.py, tests/simulation_quality/test_quality_hub_integration.py
## Completion Summary
Done in the observability hotfix batch (one PR).
