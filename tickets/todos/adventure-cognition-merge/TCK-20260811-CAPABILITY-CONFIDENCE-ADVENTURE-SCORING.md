---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING
phase: open
date: 2026-08-11
tags: [cognition, self-model]
---

# TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING

## Title
Wire capability-estimate-driven confidence into adventure route scoring

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Deepen adventure's internal reasoning by making route confidence reflect capability-estimate-driven data from CapabilityEstimateService instead of a flat generation-time confidence constant. Investigation found this is a blocked/larger-prerequisite idea, not a simple wire-up: CapabilityEstimateService is structurally empty in the live pipeline today, so this ticket must resolve that prerequisite as part of its own scope, disclosed explicitly rather than silently assumed.

## Scope
- Resolve the capability_context-never-populated prerequisite: either (a) populate a real CapabilityContext upstream of SelfModelUpdatePhase, or (b) have AdventureRouteScorer call CapabilityEstimateService.estimate() itself with a route-scoped ad-hoc context, bypassing the never-populated field -- decision made explicitly, not assumed
- For a route whose family maps to a capability key, confidence_bonus reflects a real CapabilityEstimate.estimate value, not always the generation-time confidence constant
- New capability read stays the entity's own subjective belief per scoring.py's documented information-opacity boundary

## Out of Scope
- Memory-informed candidates (TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING) and relationship-aware FORM_PARTY (TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY) -- separate tickets
- Any change to AdventureGoalScorer/AdventureDecisionService's wrapper migration -- orthogonal but touches the same files; recommend landing after that migration settles

## Acceptance Criteria
- [ ] The capability_context-never-populated prerequisite gap is explicitly disclosed and resolved as part of this ticket's own scope (not silently assumed already wired)
- [ ] For a route whose family maps to a capability key, confidence_bonus reflects a real CapabilityEstimate.estimate value, not always the generation-time confidence constant
- [ ] Existing isolated CapabilityEstimateService unit tests continue to pass unchanged

## Related Tickets
None.

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/cognition/capability_estimate.py
- src/cognition/self_model_phase.py
- src/core/self_model.py
- src/domains/adventure/scoring.py

## Assumptions / Open Questions
- BLOCKED/larger-prerequisite finding: entity.self_model.capabilities.estimates is empty in production today regardless of this concern, because capability_context is never supplied to SelfModelUpdatePhase.run() at its only production call site (zero grep hits for capability_context= outside the 2 cognition files) -- this is not a simple wire-up; the prerequisite must be resolved and disclosed, not hidden
- Sequencing/merge conflict risk with the adventure/cognition wrapper migration tickets (which declare AdventureRouteScorer 'unchanged internally') -- recommend landing after those settle, or explicitly disclaim the risk if landed concurrently
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns)

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
