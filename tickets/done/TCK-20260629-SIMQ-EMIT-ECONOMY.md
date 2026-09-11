---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-ECONOMY
phase: done
date: 2026-06-29
tags: [simq, observability, event-gap, economy]
---

# TCK-20260629-SIMQ-EMIT-ECONOMY

## Title
SimQ: Emit ECONOMY Pillar Events from Intent Results

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
ECONOMY pillar requires 12 event types. Investigation found that resource_transfers are
CLEARED by ResourceTransactionPhase (economy.py:274), so EventExtractor cannot use them.
All economy events detected from `entity_updates[eid].intent_results` which survive the
pipeline. Also fixed paid_information_transaction from cognition ticket (same bug).

## Scope
7 ECONOMY events from intent_results: resource_harvested, item_crafted, shop_transaction,
trade_executed, quest_reward_dispensed, gold_sink_fired, paid_information_transaction.
Fixed paid_information_transaction detection to use intent_results instead of resource_transfers.

## Out of Scope
- `conservation_law_verified` — too high volume (every successful transaction)
- `conservation_law_violated` — covered by InvariantViolation translation layer
- `trade_executed` as P2P (not shop) — no distinct source_kind for P2P trades

## Acceptance Criteria
- [x] `resource_harvested` from intent_results.source_kind=="NODE"
- [x] `item_crafted` from intent_results.source_kind=="CRAFTING"
- [x] `shop_transaction` + `trade_executed` from "SHOP_BUY"/"SHOP_SELL"
- [x] `quest_reward_dispensed` from "QUEST"
- [x] `gold_sink_fired` from "REPAIR_FEE"/"SERVICE_FEE"/"TAX"
- [x] `paid_information_transaction` fixed to use intent_results (was broken — resource_transfers cleared)
- [x] 15 economy tests + 14 updated cognition tests; 868 total pass

## Related Stored Artifacts
- `stored_artifacts/TCK-20260629-SIMQ-EMIT-ECONOMY/`

## Files Changed
- `src/observability/event_extractor.py` — replaced resource_transfers block with intent_results loop
- `tests/unit/observability/test_event_extractor_economy.py` — new (15 tests)
- `tests/unit/observability/test_event_extractor_cognition.py` — fixed 4 paid_info tests
- `staging_artifacts/TCK-20260629-SIMQ-EMIT-ECONOMY/` → `stored_artifacts/`

## Completion Summary
Economy events live via intent_results. paid_information_transaction detection fixed from
cognition ticket (resource_transfers were cleared before EventExtractor ran). 868 tests pass.
