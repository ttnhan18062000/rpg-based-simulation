---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02
artifact_type: investigation
tags: [economy, resource, legality]
---

# investigation — TCK-20261009-SELL-IS-A-CHOSEN-ACT-PRICED-BY-MARKET-SYSTEM-EXCH-02

## Findings
Standing at a shop auto-sold the carried goods (Decision 34 removes that). SELL is now a chosen act executed by `shop_sale.py`, priced by the one market law; the shop visit ends when nothing is left to sell. Two force-full-scan tests that asserted the auto-sell were rewritten, not deleted.

## Code areas
`src/engine/shop_sale.py`, `src/engine/shop.py`, `src/engine/serves.py`, `src/engine/building_services.py`, `src/engine/building_arrival.py`, `src/engine/town_resolution.py`

## Evidence
Paired pinned measurements (5 seeds x 3 worlds, 5000 ticks, kind groups) are in the PR; the earlier 4-arm table is in the removal-evidence probes directory.
