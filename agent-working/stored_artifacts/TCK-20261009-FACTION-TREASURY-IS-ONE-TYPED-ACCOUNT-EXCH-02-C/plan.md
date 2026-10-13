---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C
artifact_type: plan
tags: [economy, resource]
---

# plan — TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C

## Approach
- `src/core/treasury.py`, one vault per region-owner bucket (sum of members' declared gold), the resolver's `treasury_update`/`SourceDebit`/INHERIT, the running per-tick treasury balance.
- `CorpseState.gold`, the dead record emptied at death, looting, escheat of a decayed body.
- Repair once / kit; gold-sink fees to the ground's owner; `RegionState.tax_share`.
- Total-coin conservation test over pinned runs; inheritance test.
