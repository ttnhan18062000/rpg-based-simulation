---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-ECONOMY
artifact_type: investigation
tags: [simq, economy, event-emission]
---

# Investigation: TCK-20260629-SIMQ-EMIT-ECONOMY

## Key finding: resource_transfers cleared after resolution

`ResourceTransactionSystem.resolve_all()` (economy.py:274) clears `resource_transfers=[]` after
processing. All `ResourceTransferIntent` objects are consumed; the `entity_updates[eid].resource_transfers`
list is empty in the refined_update passed to EventExtractor.

This also means the COGNITION ticket's `paid_information_transaction` detection via resource_transfers
was a false test (passed only because mock updates had resource_transfers populated). Fixed in this
ticket to use `intent_results` instead.

## Signal that DOES survive: entity_updates[eid].intent_results

`ResourceTransactionSystem` populates `intent_results` per entity (final_intent_results at line 273):
  `IntentResult(transaction_id, accepted: bool, reason, source_kind: str, source_id: str|int)`

`IntentResult.source_kind` is copied from `intent.source_kind` which identifies the transfer type.

## source_kind → SimQ event mapping

| source_kind | SimQ event |
|---|---|
| "NODE" | resource_harvested |
| "CRAFTING" | item_crafted |
| "SHOP_BUY", "SHOP_SELL" | shop_transaction + trade_executed |
| "QUEST" | quest_reward_dispensed |
| "REPAIR_FEE", "SERVICE_FEE", "TAX" | gold_sink_fired |
| "INFORMATION_PURCHASE" | paid_information_transaction (fixed from cognition ticket) |

## Also fixed: cognition ticket paid_information_transaction

Prior detection used resource_transfers (cleared). Now uses intent_results with
source_kind=="INFORMATION_PURCHASE". 4 cognition tests updated to use _update_with_intent_results.
