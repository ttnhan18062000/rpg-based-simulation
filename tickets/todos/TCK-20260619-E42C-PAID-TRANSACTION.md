---
status: open
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42C-PAID-TRANSACTION
phase: open
date: 2026-06-20
tags: [information-seeking, paid-transaction, lead-quality, resource-transfer, phase-4]
---

# TCK-20260619-E42C-PAID-TRANSACTION

## Title
Epic 4.2C · Paid Information Transaction + Lead Quality

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
When an entity executing an `INFORMATION_SEEKING` project reaches an `InformationProvider`, it should pay gold and receive a `LeadState` with quality proportional to the provider's reliability.

**Requires:** TCK-20260619-E42B-INFO-PROVIDER

## Scope

In the interaction phase (find `src/engine/` interaction handler):

1. Detect: seeker entity with active `INFORMATION_SEEKING` project adjacent to an `InformationProvider` entity
2. Compute: `transaction_cost = 10 * (1.0 / max(0.1, provider.reliability_score))`
3. Emit: `ResourceTransferIntent(source_kind="INFORMATION_PURCHASE", gold_delta=-int(cost), target_entity_id=provider.entity_id)`
4. On accepted: generate `LeadState` with certainty derived from reliability:
   - reliability ≥ 0.8 → `LeadCertainty.EXACT`
   - 0.5–0.8 → `LeadCertainty.APPROXIMATE`
   - < 0.5 → `LeadCertainty.VAGUE`
5. Update `UnknownFact.seeking_project_id` to `None` (project fulfilled; remove from active projects)

Gold transfer must go through authoritative apply path — conservation law applies.

## Acceptance Criteria
- `test_paid_transaction_transfers_gold_and_lead` passes
- Provider with reliability=0.9 gives EXACT lead; reliability=0.4 gives VAGUE lead
- Gold reduced via ResourceTransferIntent, not direct mutation

## Related Tickets
- TCK-20260619-E42-INFO-SEEKING (parent epic)
- TCK-20260619-E42B-INFO-PROVIDER (required)
- TCK-20260619-E42D-CONTRADICTION (blocked on this)

## Related Docs
- `docs/mechanics/03_economic_laws.md` (conservation law — paid info is an economic exchange)

## Related Code Areas
- `src/engine/` interaction handler (find provider-seeker adjacency check)
- `src/core/strategic.py` (LeadState, LeadCertainty)
- `src/core/update_models/resources.py` (ResourceTransferIntent)

## Test Summary
```bash
pytest tests/unit/cognition/test_information_seeking.py::test_paid_transaction_transfers_gold_and_lead -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
