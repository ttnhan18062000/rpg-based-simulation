---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS
artifact_type: investigation
tags: [core]
---

# Investigation — TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS

Premise re-verified and measured in the ticket body (both registries live; `src.core.items` returns None,
`src.core.registries` raises; nine consumers; in catalog mode both hold the same data). Decision (user-approved):
option 3 - keep the non-fatal None on the apply path, add a loud diagnostic. "Raise" priced out by measurement.

## Diagnostic placement: the consuming call site, not the `get` boundary
`InventoryService.can_add_items` returns False for two reasons (unknown id, capacity); a log at `ItemRegistry.get`
cannot tell them apart and would also fire for every legitimate `.get` probe (`contains`-style checks, tests,
display code). The call that matters on the apply path is `InteractionSystem.enforce` (the `can_add_items` gate).
No reason found to prefer the boundary.

## Diagnostic shape: existing rejection audit, not a new durable structure
`StateUpdate.rejections_delta` (applied to `state.rejection_registry` in `ApplyPath`) plus a typed `RejectionEvent`
with new `ReasonCode.UNKNOWN_ITEM`. Already typed, inspectable, deterministic, tick-scoped; `enforce` only reads state
and returns a refined update (no mutation). The item id is recoverable from `state.resource_nodes[target_id].yields_item`.
A hard-law check was not chosen: a content defect should not halt or flag a run as an invariant violation.

## Coverage boundary
Only the interaction call site is instrumented. The other `src.core.items` consumers (equipment, town/shop,
progression/leveling, possession) still return None silently; out of scope here, recorded in parity TOWN-195.

## Which class governs which call sites
`src.core.items.ItemRegistry` (None on unknown): inventory.py, equipment.py, town/shop.py, progression/leveling.py,
domains/progression/possession.py. `src.core.registries.ItemRegistry` (KeyError on unknown): world/providers/{services,
information,resources}.py, engine/intent/action_intent.py. The KeyError class was never reached in measured worlds.

## Post-fix check (as the dispatch asked to verify rather than assume)
After ticket TCK-20260930 the herb_patch misses are 0 in all three measured worlds (see that ticket's investigation).
No residual misses, so no new ticket from this.
