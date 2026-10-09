---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02
artifact_type: plan
tags: [economy, content, resource]
---

# plan — TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02

## Approach
- `inventory_profiles.yaml`, building till/stock declarations, `_with_declared_inventory` in the compiler.
- Divergences 2.97 (first coin) and 2.98 (minted coin).
- `deep_freeze` skips init=False fields.

## Scope guards
- Tuning profile amounts (designer, Decision 33).
- Paying minted coin from a payer (successor ticket EXCH-02-B).
