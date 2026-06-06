# Ticket: TCK-20260408-PH2-STG4-CONVERGENCE
Title: Phase 2 Stage 4: Social Convergence and Narrative Causal Analysis
Status: INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Finalize the Phase 2 Social Meaning layer by enabling active gossip, hardening the propagation of rumors, and surfacing life-level causal explanations to the user.

## Scope
- Proximity-based gossip propagation in `ActionSystem`.
- "Why Changed" causal narrative derivation in `AIPresenter`.
- Impact of reputation tags on social appraisal logic.
- Integration tests for information sharing.

## Out of Scope
- Full natural language generation (NLG) for stories.
- Dynamic faction creation or political restructuring.

## Acceptance Criteria
- [ ] Entities in proximity share salient social knowledge (gossip).
- [ ] Inspection UI shows "Recent Narrative Shifts" explaining bond changes.
- [ ] Reputation tags (e.g. `BETRAYER`) result in measurable social stance shifts.
- [ ] Integration tests verify that "Entity A knows about B's betrayal of C" after gossiping with B or C.

## Related Tickets
- TCK-20260408-PHASE2-STAGE3-ROUTINE (Done)
- TCK-20260408-PHASE2-DS (Done)

## Current Status
- [x] Context Scan
- [/] Planning
- [ ] Implementation
- [ ] Verification
