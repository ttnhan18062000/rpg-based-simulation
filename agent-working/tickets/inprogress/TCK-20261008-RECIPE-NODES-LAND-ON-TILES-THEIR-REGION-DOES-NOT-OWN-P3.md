---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3
phase: open
date: 2026-10-09
tags: [world, content, economy]
---

# TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3

## Title
Recipe resource nodes land on tiles their region owns (P3 placement default)

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Recipe nodes were placed on tiles outside the owning region, so a compiled world had producers no resident could reach by its own region's law. Placement now defaults to owned tiles; `crowded_frontier` gets the forest-edge module (Decision 35).

## Scope
- Placement default for recipe nodes: owned tiles of the declaring region.
- `wild_edge_forage` world module and its wiring into `crowded_frontier` (Decision 35).
- Divergences 2.96 (placement) and 2.99 (crowded edge).

## Out of Scope
- Changing node yields or counts.
- Any other world's layout.

## Acceptance Criteria
- [ ] Recipe nodes in a compiled world sit on tiles their region owns (tests/unit/worldbuilding/test_wild_food_node.py).
- [ ] Resolved world artifacts regenerated and consistent.
- [ ] Divergences 2.96 and 2.99 recorded with a test path.

## Related Tickets
- TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02, TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02, TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02, TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3 (one batch, one PR)
- TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B (successor)

## Related Docs
- `docs/mechanics/03_economic_laws.md`, `docs/guidelines/intentional_divergences.md` (2.96-2.103), `docs/parity_ledger/town_resource.yaml` (TOWN-200..204)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/probes/` (chain_ms.py, agg.py, table4.txt)

## Related Code Areas
`src/worldassembly/resolver.py`, `src/worldbuilding/compiler.py`, `data/content/world_modules/wild_edge_forage.yaml`

## Assumptions / Open Questions
- Free meals stay on (decision 44). SELL and WORK are dormant while an inn exists.
- Region owners are legacy faction buckets (disclosed in the PR).

## Implementation Notes
Batch 2 is one commit on `batch2-on-main` (clean re-apply of the net diff on edda25490). Paired 5-seed x 3-world measurements (arm1 main, arm6 batch 2, arm7 batch 2 with profiles not applied) are in the batch-2 PR notes.

## Test Summary
tests/unit/worldbuilding/test_wild_food_node.py

## Files Changed
See the batch-2 PR.

## Completion Summary
Pending (filled at close).
