---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260428-PH10-EXTERNAL-TRUTH
artifact_type: investigation
tags: [ph10, external, truth]
---

# Phase 10 Investigation

## Transaction Visibility
- Pipeline resolves intents but the results are lost once applied.
- Need to store these results in the `EntityState` so the UI/Inspector can show "Failed to harvest: Inventory Full".

## Conservation Proof
- We need a way to prove gold/items aren't being "leaked" or "minted" by bugs.
- A global counter that mirrors the sum of all inventories is the standard way to verify this.
