---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-TAX-IS-A-SHARE-OF-SALES-AND-WAGES-PAID-TO-THE-PLACE-HOLDERS-TREASURY-DECISION-51
artifact_type: investigation
tags: [economy, resource]
---

# investigation — TCK-20261009-TAX-IS-A-SHARE-OF-SALES-AND-WAGES-PAID-TO-THE-PLACE-HOLDERS-TREASURY-DECISION-51

## Findings
Owner decision 51 and 58: tax is a share of income, rounded down per transaction, the same for outsiders, declared once as content (`default_tax_share`). The periodic per-head levy is retired.

## Code areas
`src/engine/place_tax.py`, `src/engine/shop_sale.py`, `src/engine/work_shift.py`, `src/engine/town_resolution.py`, `data/content/defaults.yaml`
