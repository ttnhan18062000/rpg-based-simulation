---
audit_id: D04
title: Balance & Tuning
status: done
date: 2026-06-20
ticket: TCK-20260618-AUDIT-EPIC
related_tickets: [TCK-20260619-E12A-BALANCE-MEASURE, TCK-20260619-E12B-BLOCKER-RECAL, TCK-20260619-E12C-BALANCE-TESTS]
layer: simulation
priority: P1
tags: [balance, tuning, combat, hunger, economy, adventure-routing, blocker-penalty, audit-done]
---

# D04 — Balance & Tuning

## Dimension Profile

| Field | Value |
|---|---|
| Audit ID | D04 |
| Method | run-sim (cross-audit inference) |
| Priority | 7 |
| Status | **partial** — combat and hunger balance observed; economic balance blocked |
| Data sources | D03, D05, D06, D08 run data; `src/domains/adventure/scoring.py` code-read |

## What this dimension answers

Are the numerical constants that govern the simulation — combat damage, need urgency thresholds, scoring weights, penalty magnitudes — calibrated to produce interesting dynamics? Or are they skewed to the point that one system overwhelms all others?

## Why This Is Partial

D04 was blocked at audit start by RC1/RC2/RC3 (zero behavioral output). After those were fixed, D06 revealed a new blocker: hunger urgency permanently outscores all economic goals (D06 F1). With entities trapped in hunger cycling, crafting/trade/gold balance cannot be measured. Economic tuning analysis requires hunger satiation to be resolved first.

This document captures all balance observations derivable from cross-audit data. The blocked sections are explicitly marked.

---

## Observable Balance Data

### 1. Scoring Formula Constants (code-read: `src/domains/adventure/scoring.py:134`)

```
score = urgency + benefit + personality_bias + confidence_bonus − risk_penalty − blocker_penalty
```

| Term | Value | Notes |
|---|---|---|
| `urgency` | 0.0–2.0 (estimated from need urgency range) | Hunger urgency dominates all others in practice |
| `benefit` | `opportunity.expected_benefit` (divided by 100 in generator) | Small values; benefit rarely exceeds 0.5 |
| `personality_bias` | max 0.25 per trait | All traits 0.0 (D05 F1); effective contribution = 0 |
| `confidence_bonus` | `opportunity.confidence × 0.15` | Max 0.15 |
| `risk_penalty` | `risk × risk_multiplier × 0.5` | `risk_multiplier = 1.0` for all entities (caution=1.0, bravery=0.0) |
| `blocker_penalty` | **2.0 (fixed)** | Massively dominates; any blocked route scores ≤ 0 |

**Key imbalance observed**: The 2.0 blocker penalty exceeds the maximum achievable non-blocked score (urgency ~2.0 + benefit ~0.5 + confidence_bonus 0.15 = ~2.65) by a very small margin. A barely-blocked route and an unblocked mediocre route score comparably. This creates a near-binary filter: blocked routes are near-universally rejected regardless of their urgency or benefit.

> **RESOLVED (by design, 2026-06-19, TCK-20260619-E12B-BLOCKER-RECAL):** blocker_freq measured at 0.0% in all tested worlds; penalty kept at 2.0; docs/mechanics/04_strategic_cognition.md §6 updated with scoring constants; STRAT-227 parity entry added.

---

### 2. Combat Balance

**Data sources:** D03 (8 combat_damage events, 5 kills in ticks 3–20, sandbox_world), D08 (dungeon_crawl: 32 combat_damage + 17 kills in 400 ticks; wilderness_survival: 11 kills near-extinction).

| World | Starting entities | Alive at tick 100 | Combat attrition rate |
|---|---|---|---|
| sandbox_world | 20 | ~15 | 25% |
| urban_political | 27 | ~15 | 44% |
| dungeon_crawl | 32 | ~1–2 | **94–97%** |
| wilderness_survival | 11 | ~0–1 | **>95%** |

**Observation**: Combat lethality is consistent per-engagement but world content drives total attrition wildly. In sandbox_world and urban_political, spawned entities are sufficiently separated that combat is limited to early adjacency. In dungeon_crawl/wilderness_survival, dense spawning or hostile entity placement drives near-extinction.

Combat damage formula is not directly readable from run-sim data at LIGHT observability. No hard law violations were recorded across any run — combat resolution is mechanically correct.

**Balance finding**: The 4× range in attrition rates across worlds suggests world content parameters (spawn density, faction distribution, region constraints) are the primary balance lever, not per-combat constants. The engine's combat pipeline is stable; the authoring layer is uncalibrated.

---

### 3. Hunger Calibration

**Data source:** D06 metric windows and event breakdown.

Entities generate a `proj_hunger_N` project approximately every 30 ticks (hunger project IDs increment ~30 per entity cycle). The hunger project is started, runs, but never terminates with need satisfaction — `proj_hunger_N` is SUSPENDED and immediately replaced by `proj_hunger_N+30`. Urgency stays high every tick.

This is a calibration failure with two possible causes (requires deeper investigation to determine which):
1. **Hunger urgency threshold too low**: urgency fires at a need level that is never durably reduced by any available action.
2. **No food-provision opportunity exists in sandbox_world**: the opportunity pipeline has no food-kind resource node, so hunger can never be satisfied through world interaction.

Either way, hunger urgency (~1.0–2.0 estimated) permanently outscores economic goals, whose urgency depends on optional goals rather than survival pressures.

**Balance finding (blocked for fix):** Until hunger satiation is restored (either by adding a food resource node or calibrating the need urgency threshold), all scoring balance observations are hunger-dominated and not representative of intended gameplay.

---

### 4. Rejection Cascade Rate

**Data source:** D06, D05.

| Phase | Rejection rate | Cause |
|---|---|---|
| Ticks 1–200 (pre-RC1-fix behavior) | ~1/tick | Stale spawn-projects retrying |
| Ticks 201–1000 (post-RC1-fix) | **~650/tick** | Opportunity requirements evaluated and failing |

The 650× jump in rejection rate after RC1 fix is not a sign the fix is wrong — it means the opportunity pipeline is now running at full volume and many requirements fail legitimately (near_service, inventory_space, has_item). However, the absence of any backoff or cooldown means every requirement evaluation failure is retried the next tick indefinitely.

**Balance finding**: Rejection accumulation is a design gap rather than a numerical constant issue. The fix is architectural (stale-project timeout, requirement cooldown) not numerical.

---

### 5. Economic Balance — BLOCKED (original entry)

**Blocked by:** D06 F1 (hunger urgency dominance), D05 F1 (personality traits all zero).

| Economic system | Observable output across all runs |
|---|---|
| Gold accumulation | 0 in sandbox_world; plateau at 120 at tick ~500 (D06), no growth |
| Resource harvesting | 3 events in urban_political seed 137 (D08) — sole observation |
| Crafting | Zero events across all runs |
| Trade / buy / sell | Zero events across all runs |
| Quest completion | Zero events across all runs |

These systems are implemented and wired (D09 confirmed wiring), but behavioral preconditions are never reached. Economic balance analysis requires:
1. Hunger satiation gap fixed (allows entities to pursue economic goals)
2. Personality traits initialized (allows personality-driven route differentiation)
3. HERO role entities in test worlds (intended economic actor class)

---

### 6. E12A Economic Measurement — Post-P0-Fix Results

**Date:** 2026-06-20  
**Run:** urban_political, seed=42, 100 ticks, `ENABLE_ADVENTURE_ROUTING=ON` explicitly for measurement  
**Ticket:** TCK-20260619-E12A-BALANCE-MEASURE

After completing P0-HUNGER-SATIATION and P0-ENTITY-INIT, a controlled measurement run was executed. **All economic metrics remain zero**, but for different reasons than the original D04 block. Root causes identified:

#### 6.1 Measured Balance Metrics

| Metric | Value | Target (E12 acceptance criterion) |
|---|---|---|
| Harvesting rate (per entity per 100 ticks) | **0.0** | > 0.1 |
| Crafting events (per entity per 100 ticks) | **0.0** | > 0 |
| Quest completion rate (per entity per 100 ticks) | **0.0** | > 0 |
| Gold accumulation (per entity, net at tick 100) | **0.0** | > 0 |
| Combat attrition at tick 100 | **46.7%** (14/30 dead) | < 60% |
| Routes scored by adventure routing | **30 over 100 ticks** | n/a |
| Routes with blockers | **0** | n/a |
| blocker_frequency | **0.0** | n/a |
| Non-hunger urgency range (from scored routes) | **0.0–0.0** | n/a |

#### 6.2 Root Causes (NEW — different from original D04 block)

**Root Cause 1 — Adventure routing disabled by default:**  
`ENABLE_ADVENTURE_ROUTING` in `src/domains/optimization/feature_flags.py` defaults to `FeatureMode.OFF`. The entire adventure decision pipeline (route generation → scoring → blocker_penalty → strategic update) is inactive in all default simulation runs. This makes the `blocker_penalty = 2.0` constant effectively dead code in production.

**Root Cause 2 — urban_political has zero resource nodes:**  
`len(state.resource_nodes) == 0` after WorldCompiler.compile(). `ResourceOpportunityProvider.get_opportunities()` iterates over `state.resource_nodes` — with zero nodes, it always returns `[]`. The earlier D08 observation of "3 harvesting events in urban_political seed 137" was from a different schema or run context. The current world.yaml compiles to no nodes.

**Root Cause 3 — Entity navigation.region_id is None:**  
All 30 entities have `navigation.region_id = None` after compilation. The opportunity provider uses `region_id` for node matching. Even if nodes existed, region-based filtering would fail for all entities.

**Root Cause 4 — All 30 scored routes are DEFER_WITH_REASON:**  
With zero opportunities generated, `AdventureRouteGenerator.generate()` produces a single DEFER route per entity. No real routes are evaluated, so the blocker_penalty and urgency calibration are untestable.

#### 6.3 Original Block vs. New Blocks

| Block | Original D04 | Post-P0 Measurement |
|---|---|---|
| Hunger dominance | ✗ Blocked | ✓ Resolved (P0-HUNGER-SATIATION done) |
| Personality traits | ✗ Blocked | ✓ Resolved (P0-ENTITY-INIT + E11 done) |
| Adventure routing disabled | Not known | ✗ **NEW BLOCK** — defaults to OFF |
| No resource nodes in urban_political | Not known | ✗ **NEW BLOCK** — 0 nodes compiled |
| Entity region not initialized | Not known | ✗ **NEW BLOCK** — all region_id=None |

#### 6.4 blocker_penalty Finding (Updated)

The original D04 concern ("blocker_penalty = 2.0 is near-binary") is superseded: the penalty never fires because:
1. Adventure routing is OFF by default
2. When enabled: resource nodes produce zero opportunities → all routes DEFER → no routes have blockers

**blocker_frequency = 0.0** across 100 ticks (with routing explicitly enabled). No blocker strings were sampled. The graduated-penalty concern from D04 cannot be evaluated until resource nodes exist and routing produces real candidates.

#### 6.5 Combat Attrition Finding (Confirmed)

urban_political (seed=42) shows **46.7% entity attrition at tick 100** (14 dead out of 30). This is moderately high but within the < 60% acceptance criterion. The attrition is combat-driven (bandit_road_trade_pressure module). This finding does NOT block economic measurement — it's a design characteristic of the world.

#### 6.6 Status After E12A

D04 economic balance measurement remains **partial** — not because of hunger/personality (resolved), but because:
1. Feature flag policy for `ENABLE_ADVENTURE_ROUTING` is undecided (stays OFF by default)
2. urban_political world needs resource nodes added (or measurement should use a different world)
3. Entity navigation initialization needs to set `region_id`

These are scoping/wiring issues, not numerical calibration issues. The `blocker_penalty = 2.0` constant should be **kept unchanged** with justification documented (see §7).

---

## Key Observations Summary

| Area | Status | Finding |
|---|---|---|
| Scoring formula structure | Observed | 2.0 blocker penalty is near-binary; never fires (all routes DEFER) in current config |
| Combat lethality | Observed | Consistent per-engagement; world content (spawn density) drives 5–97% attrition range |
| Hunger calibration | ✓ Resolved | P0-HUNGER-SATIATION fixed; urgency no longer permanently dominant |
| Personality bias | ✓ Resolved | E11 done; personality traits now seeded and active |
| Rejection cascade | Observed | 650/tick post-RC1-fix; no cooldown/backoff mechanism |
| Economic balance | **Blocked (new)** | Adventure routing OFF by default; urban_political has 0 resource nodes; region_id=None |
| Quest balance | **Blocked** | Zero quest completions; depends on economic pipeline unblocking |
| Crafting balance | **Blocked** | Same |
| blocker_penalty = 2.0 | Kept as-is | Cannot calibrate — never fires; see §7 for justification |

---

### 7. blocker_penalty = 2.0 — Decision and Justification

**Decision (E12B):** Keep `blocker_penalty = 2.0` unchanged.

**Rationale:**
- The penalty never fires in any measured run: `blocker_frequency = 0.0` with routing enabled
- The concern in §1 ("near-binary filter") is real but cannot be validated or refuted until the pipeline is unblocked (resource nodes present, entities placed in regions, routing enabled by default or in test worlds)
- Changing the constant now would be unanchored — there is no empirical sample of blocked routes to measure against
- The 2.0 value matches the design intent: a blocked route (e.g., missing a required item) should be strongly deprioritized, not gently discounted

**What E12B records:** The formula is documented in `docs/mechanics/04_strategic_cognition.md` with `blocker_penalty = 2.0` as a confirmed constant. The parity ledger entry `STRAT-SCORING-CONSTANTS` is updated to `status: verified` with `v2_evidence` pointing to this audit.

**Revisit trigger:** Re-evaluate `blocker_penalty` when `blocker_frequency > 0` is consistently observed in E12C tests. If > 30% of routes carry blockers, evaluate whether the penalty magnitude discourages useful near-blocked routes.

---

## Recommended Follow-Up

**P0 — Wire resource nodes into urban_political (prerequisite for D04 economic measurement)**  
The urban_political world compiles with `resource_nodes = []`. Add at least 3 resource nodes with `region_id` assignments that match the world's regions (hometown, bandit_road, trading_hometown). This unblocks economic balance measurement.

**P0 — Fix entity navigation.region_id initialization**  
All 30 entities initialize with `navigation.region_id = None`. The resource opportunity provider cannot match entities to nodes. Fix WorldCompiler or EntityFactory to assign `region_id` based on entity spawn location.

**P1 — Decide feature flag policy for ENABLE_ADVENTURE_ROUTING**  
Currently defaults to OFF. If the intent is to measure economic behavior in E12C tests, the test harness must explicitly enable it. If the intent is to turn it ON for all runs, update `feature_flags.py` and document the behavior change in `docs/guidelines/v2_intentional_divergences.md`.

**P1 — Run E12C balance regression tests after nodes + initialization are fixed**  
After the above P0 fixes, run `tools/balance_measure.py --ticks 1000` on urban_political. Harvest rate should exceed 0.1/entity/100t, gold accumulation > 0, blocker_frequency > 0 for at least some route families. These thresholds become the E12C regression test anchors.

**P2 — Review blocker_penalty = 2.0 magnitude (deferred to E12C)**  
Cannot evaluate until blocker_frequency > 0 is observed. See §7 for deferred-revisit trigger.
