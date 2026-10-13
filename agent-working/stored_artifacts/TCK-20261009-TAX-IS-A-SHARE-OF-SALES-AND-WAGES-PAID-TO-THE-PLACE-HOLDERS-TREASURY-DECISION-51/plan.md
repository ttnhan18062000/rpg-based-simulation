---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-TAX-IS-A-SHARE-OF-SALES-AND-WAGES-PAID-TO-THE-PLACE-HOLDERS-TREASURY-DECISION-51
artifact_type: plan
tags: [economy, resource]
---

# plan — TCK-20261009-TAX-IS-A-SHARE-OF-SALES-AND-WAGES-PAID-TO-THE-PLACE-HOLDERS-TREASURY-DECISION-51

## Approach
- `src/engine/place_tax.py`, SELL and WAGE intents carry the tax, `RegionState.tax_share`, `default_tax_share: 0.1`.
- Retire the levy in `town_resolution.py`.
