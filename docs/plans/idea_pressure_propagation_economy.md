---
status: idea
layer: economy
authority: P2
audience: developer
maturity: idea
date: 2026-06-20
tags: [idea, pressure-propagation, economy, resource-ecology, regional-signals, macro-economy]
---

# Idea: Pressure Propagation Between Regions

> **Maturity: IDEA** — Not scheduled. Must precede E33 Macro-Economy Monitor; consider alongside E21 Resource Ecology.

> **Status review (2026-08-22):** re-investigated for staleness. E21's depletion signal and E33's monitor
> both shipped since this idea was raised, but not as unified below implies — see "Status review" note
> inside Relationship to Planned Tickets for what actually happened and what's still real.

---

## Problem

The simulation currently treats each region's resource and economic state as isolated. A resource node depleted in Region A has no mechanical effect on Region B's prices, entity migration pressure, or faction territorial decisions — even when the two regions are adjacent and the depleted resource is the primary production input for Region B's crafting economy.

Two planned tickets converge on this gap without solving it:

- **E21 Resource Ecology** adds per-node depletion/regeneration state (`current_charges`, `regen_rate_per_tick`). This creates the signals, but they remain local.
- **E33 Macro-Economy** adds aggregate monitoring metrics (Gini coefficient, transaction velocity, price indices). But a monitor that sees each region's numbers in isolation cannot detect the *cause* of a price spike — it only sees the symptom.

Without propagation, the macro-economy monitor measures noise, not signal. A price spike in Region B caused by Region A's depletion looks identical to a price spike from internal demand shock. The governance layer (E33's `EconomyHealthMonitor`) cannot distinguish them and cannot trigger the correct response.

The `pressure_signals: Dict[str, float]` field already exists on `AuthoritativeState` but is currently unrouted between regions — it is the architectural stub for this idea.

---

## Idea

Implement a **pressure propagation layer** that routes resource depletion signals, economic stress signals, and migration pressure signals from their source region to adjacent regions through the world topology graph.

### Pressure signal types

| Signal type | Source event | Propagated effect |
|---|---|---|
| `resource_scarcity` | Node depleted below 20% charges | Adjacent regions: price index for that commodity rises; entity harvest routes to adjacent regions score higher |
| `economic_stress` | Gini > 0.6 or velocity drop > 30% | Adjacent regions: MERCHANT entity trade routes to stressed region score higher (opportunity signal) |
| `migration_pressure` | Entity needs unsatisfied for N ticks | Neighboring regions: their `density` signal rises, affecting faction territory evaluation |
| `calamity_aftermath` | Calamity resolved | Surrounding regions: resource regen rates temporarily elevated (recovery signal) |

### Propagation mechanics

Propagation follows the world topology graph (sovereignty edges already defined in `docs/mechanics/06_worldbuilding_foundation.md`). Signal strength decays with topological distance:

```
signal_strength_at_neighbor = source_signal * adjacency_weight * decay_factor^hop_count
```

`adjacency_weight` comes from the existing sovereignty edge attributes. `decay_factor` defaults to 0.5 per hop (configurable per world). Signals below a minimum threshold (default: 0.05) are dropped rather than propagated further.

### Integration with the existing `pressure_signals` field

`AuthoritativeState.pressure_signals: Dict[str, float]` receives the computed pressure values each governance tick. The key format is `"{signal_type}:{source_region_id}"`. Existing consumers of `pressure_signals` (currently none) would read from here.

### Pipeline placement

Pressure propagation runs as a **governance phase step**, after `EconomyHealthMonitor` samples per-region metrics and before route scoring begins. This ensures entities see propagated pressure in the same tick it is generated.

---

## Relationship to Planned Tickets

**Status review (2026-08-22).** Both tickets below have since shipped — read this note before either section,
since the original "missing link" framing describes a gap that no longer exists in the form predicted:

- `TCK-20260628-E21E-CROSS-REGION-PRESSURE` (DONE, 2026-06-28) shipped resource-scarcity propagation, via
  `RegionalPressureModel.propagate_cross_region()` (`src/domains/world_emergence/models.py:148-235`). It is
  narrower than this doc's design: bounding-box gap adjacency (`ADJACENCY_GAP=50`) rather than the
  sovereignty-graph edges this doc assumed, a flat `PROPAGATION_FACTOR=0.30` rather than
  `decay_factor^hop_count`, and single-hop only — no multi-hop chain. `AuthoritativeState.pressure_signals`
  (still at `src/core/state.py:1144`) remains the unused stub this doc described; the real implementation
  writes typed `RegionalPressure`/`ServicePressure` records instead, not that dict.
- `TCK-20260619-E33A-HEALTH-MONITOR` (DONE) shipped `EconomyHealthMonitor` (`src/economy/health_monitor.py`).
  **Confirmed by direct grep: `health_monitor.py` never references `RegionalPressure`,
  `propagate_cross_region`, or `pressure_signals`.** The monitor and the propagation layer were built
  independently, in the same repo, and were never wired together — this doc's predicted "HIGH RISK if E33
  ships before propagation is wired" happened almost exactly as warned, just silently rather than as a
  blocking failure.

**What's still real and worth a ticket:** (1) wire `RegionalPressureModel`'s existing `resource` propagation
output into `EconomyHealthMonitor` so Gini/velocity metrics gain a causal explanation — this is a much
smaller task than the "build propagation from scratch" framing below implies; (2) the `economic_stress`,
`migration_pressure`, and `calamity_aftermath` signal types in the table above were never built — only
`resource_scarcity` shipped, and only as an unwired signal.

The two subsections below are kept as originally written for their diagnostic value (the exact language
that predicted the gap correctly), but their "planned ticket" framing is now historical — read them as
"what was predicted, and what actually happened" rather than as current planning.

### E21-RESOURCE-ECOLOGY (missing link — signals created but not routed) — historical, E21 shipped 2026-06-28

E21 plans: *"Add durable fields to `ResourceNodeState`: `current_charges`, `max_charges`, `regen_rate_per_tick`, `last_harvested_tick`; Wire `ResourceEcologyService` to apply depletion on harvest and regeneration on world tick."*

E21 creates the authoritative depletion signal. Without propagation, that signal exists in `ResourceNodeState` but affects only the node's own region. Adjacent regions do not see the scarcity and do not adjust their behavior.

**Impact on E21**: additive. E21 should expose a `ResourceDepletionEvent` (or similar typed record) when a node crosses the 20% threshold. Pressure propagation subscribes to these events in the governance phase. The event schema should be defined in E21 scope to avoid a later breaking change.

**Risk level: LOW for E21 independently. HIGH if E33 ships before propagation is wired.** The EconomyHealthMonitor will see regional metrics that are causally disconnected, making its Gini/velocity signals uninterpretable.

### E33-MACRO-ECONOMY (missing link — monitor without causality) — historical, E33A shipped, still disconnected today

E33 plans: *"EconomyHealthMonitor: runs as governance phase step; samples gold distribution, transaction volume, price indices per region per tick-window; Metrics: Gini coefficient, transaction velocity, average price index per commodity, gold creation vs destruction rate."*

The EconomyHealthMonitor measures outcomes (Gini, velocity) but has no causal model. Without pressure propagation, it cannot answer: *why* is transaction velocity falling in Region B? Is it depletion-driven scarcity from Region A, or internal faction conflict? The monitor's governance triggers (presumably: high Gini → intervention, low velocity → stimulus) will misfire if the root cause is cross-regional.

**Impact on E33**: HIGH RISK. Pressure propagation is the causal layer that makes `EconomyHealthMonitor` metrics interpretable. The monitor should read `pressure_signals` from `AuthoritativeState` alongside its sampled metrics, and report them together. If this is not in scope for E33, the monitor's governance triggers should be marked as advisory-only until propagation is wired.

**Recommendation**: implement pressure propagation as part of E33 scope, or as a prerequisite ticket `E33-PRE-PRESSURE-PROPAGATION` that E33 declares as a dependency.

---

## Open Questions

- What is the right decay factor and minimum threshold? Too aggressive decay means distant regions never react; too little means every depletion ripples globally.
- Should propagation be synchronous (computed each governance tick) or asynchronous (batched every N ticks for performance)?
- How does propagation interact with territorial boundaries (E53 Faction Diplomacy)? Allied regions may propagate at full strength; hostile regions may block signals.
- Does pressure propagation need to be deterministic-seeded (uses `DeterministicRNG`) to satisfy replay constraints?

---

*Raised: 2026-06-20. HIGH RISK if E33 implements EconomyHealthMonitor before this propagation layer is in place.*
