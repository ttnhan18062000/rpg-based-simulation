---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C
artifact_type: investigation
tags: [economy, resource]
---

# investigation — TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C

## Findings
The treasury was an untyped `global_resources` key written three ways, read one way and left orphaned for most catalog factions; an inheritance copied items and dropped gold; a repair charged twice; gold-sink fees, building tax, maintenance, kill gold and quest gold minted or destroyed coin. `src/core/treasury.py` gives the treasury one key scheme, a typed transfer and the total-coin invariant; the resolver gains a treasury channel, a source debit and an INHERIT transfer; coin is conserved over a pinned run.

## Code areas
`src/core/treasury.py`, `src/core/conservation.py`, `src/engine/economy.py`, `src/engine/pipeline.py`, `src/systems/lifecycle_systems/lifecycle.py`, `src/engine/apply_plan.py`, `src/engine/world_dynamics.py`, `src/worldbuilding/compiler.py`
