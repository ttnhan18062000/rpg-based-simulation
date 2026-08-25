---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING
phase: open
date: 2026-08-24
tags: [adventure, cognition]
---

# TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING

## Title
Wire Causal Memory into Adventure Route Scoring (Expertise Earned Through Living)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
MemoryUpdatePhase has zero call sites, so its consumer (AdventureRouteScorer.score()) already reads only 2 of 10 possible advice values from causal memory that never actually populates. The author wants MemoryUpdatePhase wired in, at the proposed insertion point between PP-02 and PP-03.

## Scope
- Register MemoryUpdatePhase's call site in src/engine/pipeline.py between actor_validity (PP-02) and self_model (PP-03) for all active/alive entities
- Build at least one real, live trigger_event producer (e.g. combat_loss) that feeds a genuine in-tick event, not just test dicts
- Redesign/loop MemoryUpdatePhase.run()'s single trigger_event-dict-matched-by-entity_id signature so multiple entities triggering in the same tick are all updated
- Verify in an end-to-end scenario that after a real triggering event, entity.cognition.memory.causal.entries becomes non-empty and AdventureRouteScorer.score() produces a nonzero memory_adjustment
- Correct docs/simulation/domains/memory_contract.md's Domain Interactions row, which currently falsely asserts causal memory already feeds route scoring in production

## Out of Scope
- The 7 orphaned mechanisms tracked by TCK-20260824-WIRE-ORPHANED-MECHANISMS -- MemoryUpdatePhase is explicitly excluded from that ticket's scope and owned here
- Extending the future_advice->RouteFamily mapping beyond the current 2-of-10 advice values read -- that is TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING's own separately-flagged, larger scope; this ticket should decide whether to extend that mapping or purely wire the phase, not silently do both

## Acceptance Criteria
- [ ] pipeline.py registers MemoryUpdatePhase's call site between actor_validity (PP-02) and self_model (PP-03) for all active/alive entities
- [ ] At least one real, live trigger_event producer feeds a genuine in-tick event, not just test dicts
- [ ] In an end-to-end scenario, after a real triggering event, entity.cognition.memory.causal.entries becomes non-empty and AdventureRouteScorer.score() produces a nonzero memory_adjustment
- [ ] MemoryUpdatePhase.run()'s signature is redesigned/looped so multiple entities triggering in the same tick are all updated

## Related Tickets
- TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING
- TCK-20260529-COG-PHASE13-MEMORY
- TCK-20260824-WIRE-ORPHANED-MECHANISMS

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/engine/kernel.md
- docs/simulation/domains/memory_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/memory/phase.py
- src/domains/adventure/scoring.py
- src/domains/memory/attribution.py
- src/core/cognition.py
- src/engine/pipeline.py
- src/engine/combat.py

## Assumptions / Open Questions
- Whether to extend the future_advice->RouteFamily mapping beyond 2-of-10 values in this same ticket, or purely wire the phase and leave the mapping extension for TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING, is an open decision
- Building a genuine trigger_event source (combat_loss/failed_search/failed_craft/party_abandoned) is materially larger than "add one phase call" and should be scoped/estimated accordingly
- layer set to `strategy` (bounded cognition / goal hierarchy) rather than `engine`, since the substantive scope is causal memory driving cognitive route advice, not the tick-loop mechanics itself; the pipeline.py call-site registration is a means to that end

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
