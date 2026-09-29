---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-CHRONICLE-SURPRISE-SIGNIFICANCE-TERM
phase: open
date: 2026-08-22
tags: [observability]
---

# TCK-20260822-CHRONICLE-SURPRISE-SIGNIFICANCE-TERM

## Title
Chronicle Surprise-Significance Term from Decision Trace Data

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add a surprise term to Chronicle's event significance scoring, derived from how much an entity's actually-selected decision diverged from its scored alternatives. Investigation corrects the original proposal's framing: the quoted "current formula" (severity+entity_reach+cascade_downstream_count) was never implemented -- it was copied verbatim from a pre-implementation roadmap description, and the real, live formula is BASE_SIGNIFICANCE[event_type]+hero_bonus in src/domains/chronicle/significance.py (shipped under E51A). Critically, this ticket does NOT depend on the sibling ring-buffer ticket's unbuilt work: decision_trace.jsonl's routes[] array (up to 5 scored candidates with score+selected flag, already shipped) has enough data today to compute |actual_score - mean_candidate_score| via a tick+entity_id join, since Chronicle compilation is post-run/offline and can read the already-shipped file+index directly.

## Scope
- Add surprise_term computation to significance.py, sourced from a (tick, entity_id) join against decision_trace.jsonl's routes[] array
- Gate the surprise term behind an explicit opt-in flag, off by default
- Handle missing/partial decision_trace entries gracefully -- fall back to exactly the current base+hero_bonus value
- Add a run_dir/decision_trace path parameter to the Chronicle compiler's read path, with graceful handling when the file or index doesn't exist
- Add unit tests covering both a clustered-candidates case (low surprise) and a forced/cornered case (high surprise)

## Out of Scope
- Building the sibling ring-buffer ticket's IntentionSnapshot type -- not required; decision_trace.jsonl already provides sufficient data for this ticket
- Social memory decision_context attachment (separate ticket TCK-20260822-SOCIAL-MEMORY-DECISION-CONTEXT)
- Faction-level event surprise scoring -- the routes[] join is entity-scoped only via subject_id; faction events (dual-faction subject_id) remain on the base formula, a documented coverage gap, not solved here
- Making mean_candidate_score a true population mean -- routes[] is capped at 5 candidates, so the mean is an approximation and must be documented as such, not corrected

## Acceptance Criteria
- [ ] Corrected baseline documented: significance.py's actual current formula is BASE_SIGNIFICANCE[event_type] + hero_bonus; the proposal's originally quoted severity+entity_reach+cascade_downstream_count formula was never implemented and must not be treated as the formula being modified
- [ ] This ticket does not depend on the sibling ring-buffer/IntentionSnapshot work -- decision_trace.jsonl's routes[] array (up to 5 scored candidates, score+selected flag) already contains sufficient data today via a tick+entity_id join against the already-shipped decision_trace.jsonl + tick_index.py
- [ ] Given a NarrativeLedgerEntry with an int-castable subject_id whose (tick, entity_id) has a matching decision_trace.jsonl entry, score() returns base+hero_bonus+surprise_term where surprise_term = clamp(|actual_score - mean(routes[].score)| * weight, 0, cap), with total still capped at 1.0
- [ ] Given a NarrativeLedgerEntry with no matching decision_trace entry (faction event, OBS_DECISION_TRACE=OFF, entity not routed that tick, or dropped by the accepted async crash-loss/queue-overflow window), score() returns exactly the current base+hero_bonus value with zero behavior change, verified by all existing tests in tests/unit/domains/chronicle/test_significance.py and test_chronicle_compiler.py continuing to pass unmodified
- [ ] Surprise term is off by default behind an explicit opt-in flag; score() remains pure/stateless with no engine imports and no new mutable/durable state -- the decision_trace read is an external join input, not new state
- [ ] A new unit test constructs a decision_trace.jsonl fixture with routes clustered near the winner's score vs. a forced/cornered case, asserting the forced case yields a strictly higher surprise-weighted score

## Related Tickets
- TCK-20260822-STRATEGIC-INTENTION-RING-BUFFER

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/chronicle/significance.py
- src/domains/chronicle/compiler.py
- src/domains/chronicle/grouper.py
- src/observability/cognition/decision_trace_writer.py
- src/observability/cognition/tick_index.py
- src/domains/campaigns/state.py
- src/domains/adventure/scoring.py

## Assumptions / Open Questions
- routes[] is capped at 5 scored candidates, not the full candidate set -- mean_candidate_score is an approximation of a true population mean and must be documented as such
- Coverage is partial: surprise term is only computable for entity-scoped events with a same-tick AdventureGoalScorer decision trace entry; most faction-level events always fall back to the base formula
- Chronicle compiler currently reads only campaign_state.narrative_ledger in-memory with zero decision_trace.jsonl dependency -- this introduces Chronicle's first cross-artifact read dependency and needs graceful handling when the file/index doesn't exist

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
