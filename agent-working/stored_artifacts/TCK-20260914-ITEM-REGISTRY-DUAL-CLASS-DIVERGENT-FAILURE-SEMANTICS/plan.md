---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS
artifact_type: plan
tags: [core]
---

# Plan — TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS

1. `InventoryService.unknown_item_ids(stacks)` pure read helper (`src/core/inventory.py`).
2. `ReasonCode.UNKNOWN_ITEM` (`src/core/enums.py`).
3. In `InteractionSystem.enforce`, when `can_add_items` is False and `unknown_item_ids` is non-empty, add
   `rejections_delta["INTERACTION_UNKNOWN_ITEM"]` + a `RejectionEvent`; keep the reset unchanged.
4. Tests: unknown recorded and still non-fatal; capacity not reported as unknown; success records nothing;
   purity and determinism; helper.
5. Document call-site governance in this investigation and parity TOWN-195; divergence section 2.60.
6. Out of scope: consolidating the two classes; instrumenting the other `src.core.items` consumers.
