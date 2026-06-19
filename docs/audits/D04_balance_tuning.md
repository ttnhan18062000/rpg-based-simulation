---
audit_id: D04
title: Balance & Tuning
status: partial
date: 2026-06-19
ticket: TCK-20260618-AUDIT-EPIC
layer: simulation
priority: P1
tags: [balance, tuning, combat, hunger, economy, audit-partial]
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

### 5. Economic Balance — BLOCKED

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

**Recommendation**: Defer economic balance audit to after D05 F1 (personality seeding) and D06 F1 (hunger satiation) are fixed. Use urban_political as the audit world — it already produced the only observed harvesting events.

---

## Key Observations Summary

| Area | Status | Finding |
|---|---|---|
| Scoring formula structure | Observed | 2.0 blocker penalty is near-binary; personality bias term inert (all traits zero) |
| Combat lethality | Observed | Consistent per-engagement; world content (spawn density) drives 5–97% attrition range |
| Hunger calibration | Observed | Hunger never satisfied; urgency permanently high; dominates scoring every tick |
| Rejection cascade | Observed | 650/tick post-RC1-fix; no cooldown/backoff mechanism |
| Economic balance | **Blocked** | Zero observable economic activity; requires hunger + personality fixes first |
| Quest balance | **Blocked** | Zero quest completions; same blocker as economic balance |
| Crafting balance | **Blocked** | Same |

---

## Recommended Follow-Up

**P0 — Resolve hunger satiation (prerequisite for D04 completion)**
Add a food-resource opportunity to sandbox_world and urban_political, or calibrate need urgency so completing a hunger project reduces need score durably. This unblocks the entire economic balance audit.

**P1 — Audit economic balance after hunger fix using urban_political**
urban_political is the best world for this — it has buildings (enabling services), resource nodes, and has already produced `harvesting` events. Run 1,000-tick urban_political sim after hunger fix and measure gold accumulation rate, harvesting frequency, crafting conversion, quest completion rate.

**P1 — Review blocker_penalty = 2.0 magnitude**
The fixed 2.0 penalty should be compared against the realistic score range. If max non-blocked score is ~2.65, a 2.0 penalty may be too severe — any opportunity with a minor blocker (missing 1 gold) is effectively eliminated regardless of its urgency. Consider a graduated penalty or a separate "preferred but blocked" scoring track.
