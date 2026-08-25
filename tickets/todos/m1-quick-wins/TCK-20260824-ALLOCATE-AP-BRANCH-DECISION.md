---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260824-ALLOCATE-AP-BRANCH-DECISION
phase: open
date: 2026-08-24
tags: [progression]
---

# TCK-20260824-ALLOCATE-AP-BRANCH-DECISION

## Title
Decide the Fate of the Unreachable ALLOCATE_AP Branch

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
A real, unconditional ALLOCATE_AP branch exists with two live entry points, but nothing has ever constructed a payload that reaches it. The author wants a decision: wire a real producer, or leave it as intentionally-dormant scaffolding and document why.

## Scope
- Produce a decision doc stating wire-vs-dormant for the ALLOCATE_AP branch, citing SUB-376/ENTITY-008 evidence
- If wire: demonstrate a real (non-mocked) Kernel.tick_once() run reaching execute_allocate_ap, and update SUB-376's v2_evidence
- If dormant: add a docs/guidelines/intentional_divergences.md entry, and correct or explicitly document resolver.py's cosmetic AP-decrement-with-zero-attribute-gain branch
- Explicitly resolve the disposition of AllocateAttributeAction (dead code with aptitude-multiplier logic execute_allocate_ap currently lacks) -- not left as a third silent implementation

## Out of Scope
- Reconciling all three competing AP-allocation implementations beyond picking one canonical path and stating what happens to the other two -- full consolidation work may be deferred to a named follow-up if the decision doc identifies it as nontrivial
- Any change to the aptitude-multiplier gap resolution pipeline beyond what's needed for the wire-vs-dormant call

## Acceptance Criteria
- [ ] A decision doc states wire-vs-dormant with rationale citing SUB-376/ENTITY-008
- [ ] If wire: a real (non-mocked) Kernel.tick_once() run demonstrates a live path reaching execute_allocate_ap, and SUB-376's v2_evidence is updated
- [ ] If dormant: an intentional_divergences.md entry is added, and resolver.py's cosmetic branch is corrected or documented as intended
- [ ] The disposition of AllocateAttributeAction is explicitly resolved (wired, deleted, or documented), not left as an undecided third implementation

## Related Tickets
- TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP
- TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP
- TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION

## Related Docs
- docs/parity_ledger/substrate.yaml
- docs/event_ledger/entity.yaml
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/domain/core_actions.py
- src/engine/domain/action_router.py
- src/engine/intent/action_intent.py
- src/engine/domain_logic.py
- src/domains/progression/resolver.py
- src/domains/progression/generator.py
- src/domains/progression/gaps.py
- src/actions/attributes.py

## Assumptions / Open Questions
- Whether resolver.py's cosmetic branch remaining live (if dormant is chosen) is acceptable is an open call the decision doc must make explicit
- Full reconciliation of all three AP-allocation implementations may be out of scope pending the decision doc's own assessment of effort

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
