---
status: open
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33C-GOLD-SINK
phase: open
date: 2026-06-20
tags: [macro-economy, gold-sink, authoritative-pipeline, phase-3]
---

# TCK-20260619-E33C-GOLD-SINK

## Title
Epic 3.3C · Gold Sink Mechanisms

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
On `INFLATION_SPIRAL` alert: trigger gold sinks via authoritative pipeline. Three mechanisms: equipment degradation cost, service fees, tax events. All must satisfy conservation laws (Chapter 03 economic laws).

**Requires:** TCK-20260619-E33B-ALERTS-REST

## Scope

Three gold sink mechanisms triggered when `INFLATION_SPIRAL` alert fires:

1. **Equipment degradation cost**: equipment with `durability < 50%` incurs a per-tick gold maintenance fee. Apply via `ResourceTransferIntent(source_kind="REPAIR_FEE", gold_delta=-N)`.

2. **Service fees**: shops increase service fee by 10% when `INFLATION_SPIRAL` is active. Applied via existing shop pricing logic.

3. **Tax events**: regional governance emits a periodic tax: `ResourceTransferIntent(source_kind="TAX", gold_delta=-N)` for entities above the Gini-adjusted gold threshold. Gold goes to a regional treasury (tracked as a sentinel entity or world account).

**Conservation law**: gold must come from and go to defined accounts. Do NOT create or destroy gold. Tax gold goes to treasury; fees go to treasury; treasury can be redistributed via services.

## Acceptance Criteria
- Gold_creation_rate decreases in 200-tick window after INFLATION_SPIRAL sink fires
- Gold sinks go through authoritative pipeline (no direct mutation)
- `test_gold_sink_reduces_accumulation_rate` passes

## Related Tickets
- TCK-20260619-E33-MACRO-ECONOMY (parent epic)
- TCK-20260619-E33B-ALERTS-REST (required)
- TCK-20260619-E33D-REP-DISCOUNTS (can start in parallel after E33B)

## Related Docs
- `docs/mechanics/03_economic_laws.md` (atomic conservation — gold must be conserved in sinks)

## Related Code Areas
- `src/engine/` (authoritative pipeline — find correct phase for fee/tax injection)
- `src/domains/economy/` or `src/systems/economy_systems/` (shop pricing)

## Test Summary
```bash
pytest tests/integration/scenarios/test_macro_economy.py::test_gold_sink_reduces_accumulation_rate -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
