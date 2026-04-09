# Ticket TCK-20260410-PH3-STRATEGIC-KNOWLEDGE

## Request Summary
Implement Phase 3: Strategic Knowledge & Blockers. This involves expanding the strategic layer to handle structural uncertainty (Leads) and detecting stalled progress (Blockers). The goal is to move AI beyond binary "success/fail" and into a state of active inquiry and detour-based problem solving.

## Scope
- Update `LeadRecord` and `BlockerRecord` models in `strategy.py`.
- Implement **Blocker Detection** logic in `StrategicEvaluatorService`.
- Implement **Strategic Detour** generation (e.g., Knowledge Blocker -> Search Lead -> Investigation Detour).
- Extend `KnowledgePropagationService` to share strategic `LeadRecord` objects.
- Implement tactical `INVESTIGATE` goal logic.
- Verify with `tests/ai/test_strategic_uncertainty.py`.

## Out of Scope
- Party-based coordination (Phase 4).
- Causal event interpretation (Phase 5).

## Acceptance Criteria
- AI entities detect when their current objective is "blocked."
- Entities with discovery projects but no location correctly seek out "Leads" via gossip.
- Structured Leads correctly bias investigation of candidate areas.
- Strategic Knowledge survives snapshots and authoritative application.
- `tests/ai/test_strategic_uncertainty.py` passes.

## Related Tickets
- TCK-20260409-PH1-STG1-STRATEGIC-STATE (DONE)
- TCK-20260409-PH2-STRATEGIC-APPRAISAL (DONE)

## Related Docs
- thinking_high_level_implementation.md

## Current Status
INPROGRESS
