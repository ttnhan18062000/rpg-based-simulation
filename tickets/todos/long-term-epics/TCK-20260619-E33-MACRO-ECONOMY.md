---
status: open
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E33-MACRO-ECONOMY
phase: open
date: 2026-06-19
tags: [macro-economy, inflation, gold-sink, health-metrics, economic-monitoring, epic, phase-3]
---

# TCK-20260619-E33-MACRO-ECONOMY

## Title
Epic 3.3 · Macro-Economy Health Metrics

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Per-transaction conservation laws are solid and dynamic pricing exists for calamity/survival pressure. However, there is no inflation detection, no gold-sink mechanism, and no dead-economy signal. The "infinite shop, frozen economy" failure mode is documented but undetected. Reputation-based shop discounts remain explicitly unsupported in `known_limitations.md`.

Score: 7/10 · Effort: M · Source: `docs/plans/engine_future_epics_roadmap.md` § C

## Scope
- **Prerequisites:** TCK-20260619-E32-CAMPAIGN-RUNTIME (multi-episode span needed to see macro trends); TCK-20260619-P0-HUNGER-SATIATION (economic activity must be non-zero before monitoring is meaningful)
- `EconomyHealthMonitor`: runs as a governance phase step; samples gold distribution, transaction volume, price indices per region per tick-window
- Metrics tracked: Gini coefficient (gold inequality), transaction velocity (trades/tick/region), average price index per commodity, gold creation vs. destruction rate
- Alert conditions: `DEFLATION_RISK`, `INFLATION_SPIRAL` (price index growing >X%/100 ticks), `ECONOMIC_COLLAPSE` (region zero-transaction for 200 ticks), `GOLD_HOARDING` (Gini > 0.8)
- Alert events emitted to `simulation_events.jsonl`; health status in `metric_windows.jsonl`
- REST: `GET /api/v1/economy/health` — current health state per region
- Gold sink mechanisms (triggered on INFLATION_SPIRAL): equipment degradation cost, service fees, tax events
- Reputation-based shop discounts (close the known_limitations.md gap)
- Child tickets: (a) EconomyHealthMonitor + metrics, (b) alert events + REST, (c) gold sink mechanisms, (d) reputation discounts

## Out of Scope
- Faction-level economic control (Phase 5)
- Player economy dashboard
- Financial instruments / derivatives

## Acceptance Criteria
- A 2000-tick run produces at least one `ECONOMIC_ALERT` event
- Gold sink mechanisms fire and demonstrably reduce gold accumulation rate in the following 200-tick window
- `GET /api/v1/economy/health` returns current health state per region

## Related Tickets
- TCK-20260619-P0-HUNGER-SATIATION (prerequisite: economic activity must be non-zero)
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite for multi-episode macro trends)
- TCK-20260619-E21-RESOURCE-ECOLOGY (resource scarcity signals feed into economic health)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` § Macro-Economy Health Metrics
- `docs/mechanics/03_economic_laws.md` (add gold-sink mechanics section)
- `docs/mechanics/regional_sovereignty.md` § 2 (Governance/Economic Control — update with health monitor)
- `docs/plans/long_term_development_roadmap.md` § Epic 3.3
- `docs/engine/known_limitations.md` (remove "reputation discounts unsupported" claim on completion)
- `docs/parity_ledger/town_resource.yaml` (economic health monitoring entries — add as `verified`)
- New doc: `docs/economy/macro_economy_contract.md` (EconomyHealthMonitor metrics, alert conditions, gold-sink triggers)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260425-PH6-M4-ECONOMY/`

## Related Code Areas
- `src/engine/` (governance phase — where EconomyHealthMonitor runs)
- `src/observability/events.py:L54` (SimulationEvent — add alert event kinds)
- `src/core/state.py` (entity gold/inventory state for Gini calculation)

## Assumptions / Open Questions
- Which governance phase is appropriate for EconomyHealthMonitor? Check `src/engine/governance_logic.md` contract for insertion rules
- What does "transaction velocity" mean in current state? Check if there's an existing trade event that can be counted

## Implementation Notes
Monitoring-first: implement metric collection and alerting before gold sinks. Gold sink mechanisms (degradation, fees, taxes) must go through the authoritative mutation pipeline — do not directly decrement gold. Reputation discounts close an explicitly documented gap in known_limitations.md; update that doc on completion.

After implementation: create `docs/economy/macro_economy_contract.md`. Update `docs/mechanics/03_economic_laws.md` with gold-sink mechanic documentation. Remove the "reputation discounts unsupported" claim from `docs/engine/known_limitations.md`. Update `docs/parity_ledger/town_resource.yaml`. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/economy/test_economy_health_monitor.py`:
  - `test_gini_coefficient_computed_correctly()` — unit test with known gold distribution; assert Gini value within 0.01 of expected
  - `test_inflation_spiral_alert_emitted()` — inject rapid gold creation; run 2000 ticks; assert INFLATION_SPIRAL event in `simulation_events.jsonl`
  - `test_economic_collapse_alert_on_zero_transactions()` — zero-transaction region for 200 ticks; assert ECONOMIC_COLLAPSE event
- New file `tests/integration/scenarios/test_macro_economy.py`:
  - `test_gold_sink_reduces_accumulation_rate()` — trigger INFLATION_SPIRAL; assert gold_creation_rate decreases in next 200-tick window
  - `test_reputation_discount_applies()` — entity with high Faction A reputation; assert lower price at Faction A shop vs. neutral entity

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
