---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02
phase: open
date: 2026-10-09
tags: [economy, content, resource]
---

# TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02

## Title
First coin is declared world content (building tills and stock, inventory profiles applied at compile)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
No coin existed at the start of a compiled world except what a spawn happened to carry. Buildings now declare tills and stock and species/archetypes declare inventory profiles that the compiler applies at spawn; the minted coin is disclosed (divergence 2.98).

## Scope
- `inventory_profiles.yaml`, building till/stock declarations, `_with_declared_inventory` in the compiler.
- Divergences 2.97 (first coin) and 2.98 (minted coin).
- `deep_freeze` skips init=False fields.

## Out of Scope
- Tuning profile amounts (designer, Decision 33).
- Paying minted coin from a payer (successor ticket EXCH-02-B).

## Acceptance Criteria
- [ ] A compiled world's buildings and residents start with their declared coin and stock (tests/unit/worldbuilding/test_first_coin_is_declared_content.py).
- [ ] Conservation holds with the declared coin.
- [ ] Pinned paired measurement (arm1 vs arm6 vs arm7 profiles-off ablation) reported to rpg-planner.

## Related Tickets
- TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02, TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02, TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02, TCK-20261008-RECIPE-NODES-LAND-ON-TILES-THEIR-REGION-DOES-NOT-OWN-P3 (one batch, one PR)
- TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B (successor)

## Related Docs
- `docs/mechanics/03_economic_laws.md`, `docs/guidelines/intentional_divergences.md` (2.96-2.103), `docs/parity_ledger/town_resource.yaml` (TOWN-200..204)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/probes/` (chain_ms.py, agg.py, table4.txt)

## Related Code Areas
`src/worldbuilding/compiler.py`, `src/worldassembly/*`, `src/content/schema.py`, `src/core/immutability.py`, `data/content/entities/inventory_profiles.yaml`

## Assumptions / Open Questions
- Free meals stay on (decision 44). SELL and WORK are dormant while an inn exists.
- Region owners are legacy faction buckets (disclosed in the PR).

## Implementation Notes
Batch 2 is one commit on `batch2-on-main` (clean re-apply of the net diff on edda25490). Paired 5-seed x 3-world measurements (arm1 main, arm6 batch 2, arm7 batch 2 with profiles not applied) are in the batch-2 PR notes.

## Test Summary
tests/unit/worldbuilding/test_first_coin_is_declared_content.py

## Files Changed
See the batch-2 PR.

## Completion Summary
Pending (filled at close).
