---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B
artifact_type: investigation
tags: [economy, resource]
---

# investigation — TCK-20261009-MINTED-KILL-AND-QUEST-COIN-IS-PAID-BY-A-PAYER-EXCH-02-B

## Findings
Owner decisions 38 and 58: a kill grants experience only; the dead entity's coin moves to its body and a looter takes it; a quest reward's gold comes from a treasury, and a short treasury records a typed OwedRecord paid oldest first.

## Code areas
`src/engine/combat.py`, `src/engine/quests.py`, `src/engine/pipeline_phases/quest_opportunity_rewards.py`, `src/core/state.py`, `src/core/conservation.py`
