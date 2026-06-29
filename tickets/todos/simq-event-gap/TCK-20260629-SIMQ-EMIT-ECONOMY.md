---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-ECONOMY
phase: open
date: 2026-06-29
tags: [simq, observability, event-gap, economy]
---

# TCK-20260629-SIMQ-EMIT-ECONOMY

## Title
SimQ: Emit ECONOMY Pillar Events from Blacksmith, Shop, Gold-Sink, and Quest Reward Phases

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The ECONOMY pillar scores 12 event types. `gold_transferred` is partially covered by the
translation of `gold_transaction`. The remaining 11 types require hooks in the economy
pipeline phases: PP-07 (blacksmith/crafting), PP-21 (gold_sink), PP-24 (quest_rewards),
PP-25 (shop), PP-27 (resource_transactions).

## Scope
Add `EventRecorder.record()` calls in each economy phase for:

| Event type | Source phase | Trigger |
|---|---|---|
| `resource_harvested` | PP-27 | Entity gains items from a resource node (not gold — items) |
| `item_crafted` | PP-07 | Blacksmith or entity produces output item |
| `trade_executed` | PP-25 or PP-27 | Entity buys/sells to shop or another entity |
| `shop_transaction` | PP-25 | Specifically a shop buy/sell (distinct from P2P trade) |
| `gold_sink_fired` | PP-21 | Gold sink drains inflation pressure |
| `conservation_law_verified` | PP-27 or kernel apply | Conservation check passes (transfer balanced) |
| `conservation_law_violated` | PP-27 or kernel apply | Conservation check fails |
| `quest_reward_dispensed` | PP-24 | Quest reward (XP + items + gold) dispensed to entity |
| `paid_info_transaction` | PP-26 | Entity pays for information (also partially in SIMQ-EMIT-COGNITION — coordinate) |

Note: `resource_node_depleted` and `resource_node_regenerated` are in
TCK-20260629-SIMQ-EMIT-STATE-DIFF and TCK-20260629-SIMQ-EMIT-WORLD — do NOT re-emit here.

**Coordination note:** `paid_info_transaction` is also targeted in
TCK-20260629-SIMQ-EMIT-COGNITION. Implement in exactly one phase (PP-26) and coordinate
with that ticket so only one emission site exists.

## Out of Scope
- World ecology events (ecology_cycle_completed): TCK-20260629-SIMQ-EMIT-WORLD
- Faction economy (resource_seized): TCK-20260629-SIMQ-EMIT-FACTION
- Changing economy phase logic (emit only)

## Acceptance Criteria
- [ ] `resource_harvested` emitted from PP-27 with `{"item_type", "quantity", "node_id"}`
- [ ] `item_crafted` emitted from PP-07 with `{"item_type", "recipe_id"}`
- [ ] `trade_executed` and `shop_transaction` emitted from PP-25 (distinguish by transaction source)
- [ ] `gold_sink_fired` emitted from PP-21 with `{"amount_drained"}`
- [ ] `conservation_law_verified` / `conservation_law_violated` emitted at check site
- [ ] `quest_reward_dispensed` emitted from PP-24 with `{"quest_id", "xp", "gold", "items"}`
- [ ] No duplicate emission with TCK-20260629-SIMQ-EMIT-STATE-DIFF or TCK-20260629-SIMQ-EMIT-WORLD
- [ ] No import of `src/simulation_quality/` from economy phases
- [ ] Unit tests per phase emission site
- [ ] ECONOMY pillar shows non-zero events in calibration run

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite)
- TCK-20260629-SIMQ-EMIT-STATE-DIFF (coordinate on conservation_law events)
- TCK-20260629-SIMQ-EMIT-COGNITION (coordinate on paid_info_transaction)
- TCK-20260629-SIMQ-EMIT-WORLD (coordinate on node events)
- SIMQ-CALIBRATED-001 parity entry

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 ECONOMY
- `docs/mechanics/03_economic_laws.md` — atomic conservation and resource loop laws

## Related Code Areas
- PP-07 (blacksmith), PP-21 (gold_sink), PP-24 (quest_rewards), PP-25 (shop), PP-26 (paid_information), PP-27 (resource_transactions)
- `src/observability/events.py` — existing GoldTransactionEvent; may need ResourceHarvestEvent, etc.

## Assumptions / Open Questions
- PP-27 `resource_transactions` is the canonical harvest site (entities collect items from nodes)
- PP-25 `shop` handles NPC shop buy/sell; PP-27 handles P2P trade — verify distinction
- Conservation law check may happen inside `AuthoritativeApplyPipeline` rather than in PP-27
  specifically — verify location before adding emission hook
