---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B
phase: open
date: 2026-10-09
tags: [economy, resource]
---

# TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B

## Title
Kill and quest coin is paid by a payer, not minted

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Kill and quest rewards, and the building tax tick (+10 per functional building) and maintenance (-5 to no one), mint or destroy coin. Batch 3 (treasury) makes each a transfer from a payer (decisions 37, 38, 51), with one treasury per real faction, and settles inheritance duplication and the REPAIR double charge.

## Scope
Successor to batch 2 (divergence 2.98). Design goes to rpg-planner first.

## Out of Scope
Batch 2 content.

## Acceptance Criteria
- [ ] To be written with the batch-3 design.

## Related Tickets
- TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02

## Related Docs
- `docs/guidelines/intentional_divergences.md` 2.98

## Related Stored Artifacts
None yet.

## Related Code Areas
`src/engine/town_resolution.py`, `src/core/conservation.py`, `src/engine/gold_sink.py`

## Assumptions / Open Questions
- Phase B freeze files (state.py, inventory.py) need rpg-planner's go.

## Implementation Notes
None.

## Test Summary
None.

## Files Changed
None.

## Completion Summary
Not started.
