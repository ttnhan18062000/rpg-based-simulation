---
audit_id: D08
title: Multi-Scenario Consistency
status: done
date: 2026-06-19
ticket: TCK-20260619-AUDIT-D08-MULTI-SCENARIO
layer: simulation
priority: P2
tags: [multi-scenario, consistency, cross-world, attrition, content-balance]
---

# D08 — Multi-Scenario Consistency

## Dimension Profile

| Field | Value |
|---|---|
| Audit ID | D08 |
| Method | run-sim |
| Priority | 5 |
| Scope | `data/worlds/` — sandbox_world, dungeon_crawl, urban_political, wilderness_survival |
| Seeds | 42, 137 per world |
| Ticks | 400 each (8 runs total; sandbox_world data carried from D03/D05/D06) |

## What this dimension answers

Does simulation quality — behavioral activity, entity survival, engine stability — hold consistently across different world configurations and seeds? Or do some worlds crash, collapse, or produce qualitatively different (worse) outcomes?

## Related Dimensions

| Dimension | Relationship |
|---|---|
| D03/D06 (sandbox_world baseline) | Reference point: 15 alive, behavioral activity from tick 201 onward, 400-tick stable |
| D05 (Entity Differentiation) | urban_political produces new project kinds; helps scope D05's recommendation on HERO/class content |
| D04 (Balance & Tuning) | F2/F3 (dungeon/wilderness attrition collapse) are balance findings; D04 scope |

---

## World Inventory

| World | Entities | Regions | Buildings | Resource Nodes |
|---|---|---|---|---|
| sandbox_world | 20 | 2 | — | — |
| dungeon_crawl | 32 | 4 | 1 | 3 |
| urban_political | 27 | 3 | **7** | 0 |
| wilderness_survival | 11 | 3 | **0** | 4 |

---

## Run Summary

All 8 runs complete with `LifecycleOutcome.SUCCESS`, governor NORMAL throughout, zero hard law violations. Deterministic hashes are stable per world+seed.

| World | Seed | Alive (ticks 1–100) | Total events (400t) | Key project kinds | Final hash (16 chars) |
|---|---|---|---|---|---|
| sandbox_world | 42 | 15.3 | 70 | hunger, resolve_blocker, recover | `67d9da21bde714d9` |
| sandbox_world | 137 | 15.4 | 91 | hunger, resolve_blocker, recover | `8fdd96bd1fb071ca` |
| dungeon_crawl | 42 | **1.36** | 58 | combat_retreat, recover | `6b8729e4dc67472e` |
| dungeon_crawl | 137 | **2.62** | 58 | combat_retreat, recover | `d45f031fc6698de6` |
| urban_political | 42 | 14.33 | 61 | **town_return** (31), combat_retreat, combat_engage | `262dd6384db2974e` |
| urban_political | 137 | 15.68 | 56 | **town_return** (20), combat_retreat, **harvesting** (3) | `5900522a00973b53` |
| wilderness_survival | 42 | **0.52** | 15 | recover, combat_retreat | `882a7c657ce5b2a1` |
| wilderness_survival | 137 | **0.42** | 13 | combat_retreat | `11907fdbb4d47fdc` |

---

## Findings

### F1 — Engine Stability Consistent Across All Worlds (Positive)

All 8 runs complete successfully. Governor stays NORMAL, no hard law violations, no panics, no infinite loops. The kernel tick loop, phase pipeline, and persistence layer are robust to different world shapes (varying entity counts 11–32, regions 2–4, buildings 0–7, resource nodes 0–4). State hashes are deterministic per world+seed pair.

This is the primary consistency signal: the engine degrades gracefully even when content conditions are extreme (near-extinction entity counts).

---

### F2 — dungeon_crawl: 94–97% Entity Attrition by Tick 100

dungeon_crawl starts with 32 entities and retains only 1.36 (seed 42) and 2.62 (seed 137) by the end of the first 100-tick window — attrition rates of 94% and 92% respectively. By tick 400, fewer than 3 entities remain alive in either seed.

Event breakdown confirms combat dominance: 32 `combat_damage` + 17 `combat_kill` (seed 42); only `combat_retreat` and `recover` project kinds appear. No behavioral pipeline activity — the adventure decision phase receives no eligible entities after tick ~15 because most entities are dead.

With 32 entities and only 1 building (4 regions), entities have insufficient service access and are overwhelmed by combat early. The dungeon_crawl world spec produces a combat extinction scenario, not a crawl narrative. A functional dungeon crawler would need smaller initial populations, entity health regeneration, or dungeon-specific combat pacing.

**Severity: High** — world is unplayable in its current configuration.

---

### F3 — wilderness_survival: Near-Extinction by Tick 100

wilderness_survival starts with 11 entities and retains an average of 0.52 (seed 42) and 0.42 (seed 137) alive entities by tick 100 — effective extinction. Only 13–15 events occur across the full 400-tick run (mostly `combat_damage`). No behavioral pipeline activity. Zero buildings means the RC2 `near_service` fix has nothing to match against; all service requirements fail.

This world fulfills its "survival" theme by killing nearly everyone, but that is an authoring intent question, not an engine stability question. The engine handles it correctly — it runs to completion without error. However, a world with <1 average alive entity is unsuitable for behavioral quality observation.

**Severity: Medium** — world may be intentionally extreme, but zero buildings makes it incompatible with the current service-requirement architecture.

---

### F4 — urban_political: New Project Kinds Emerge (Positive Differentiation)

urban_political is the only non-sandbox world to exhibit behavioral pipeline activity beyond combat/recovery:

- **`town_return`**: 31 events (seed 42) and 20 events (seed 137). Entities navigate back to town — a meaningful behavioral goal driven by the world's 7 buildings providing service targets that pass the RC2 near_service check.
- **`harvesting`**: 3 events in seed 137. The first economic/resource-gathering activity observed across all audit runs (D03, D05, D06, D08). Confirms the opportunity pipeline can produce non-survival routes when the right world content exists (resource nodes + buildings in proximity).
- **`combat_engage`**: 5–10 events — entities initiating combat rather than only retreating.

This is a significant positive signal: urban_political's 7 buildings and balanced entity count (27 entities, 3 regions) create conditions where the RC-fixed adventure pipeline produces behaviorally meaningful output. It is the closest to a functioning RPG simulation among the tested worlds.

**Implication for D05 and D04**: personality/class differentiation audits and balance tuning should use urban_political as the primary world — it produces enough behavioral variety to make those measurements meaningful.

---

### F5 — Scenario World ID Not Persisted in Run Manifest

All 8 run manifests show `scenario_name: cli_default` regardless of the world used. The world ID (`dungeon_crawl`, `urban_political`, `wilderness_survival`) is not recorded in `run_manifest.json`. Run attribution requires external bookkeeping (run order) rather than reading the artifact.

This is a minor observability gap: post-hoc analysis of runs cannot identify the world from the artifact alone. A `world_id` field in `run_manifest.json` would resolve it.

**Severity: Low** — does not affect simulation correctness, only run traceability.

---

## Cross-World Behavioral Consistency Matrix

| Dimension | sandbox_world | dungeon_crawl | urban_political | wilderness_survival |
|---|---|---|---|---|
| Engine stability | ✓ SUCCESS | ✓ SUCCESS | ✓ SUCCESS | ✓ SUCCESS |
| Entity survival (tick 100) | 15/20 (75%) | 1–2/32 (5%) | 14–15/27 (54%) | 0–1/11 (5%) |
| Behavioral pipeline active | From tick 201 | Never (all dead) | From tick 201 | Never (all dead) |
| Project variety | hunger, blocker | combat only | town_return, harvest, combat | combat only |
| governor | NORMAL | NORMAL | NORMAL | NORMAL |
| Violations | 0 | 0 | 0 | 0 |

---

## Key Findings Summary

| Finding | Severity | Description |
|---|---|---|
| F1 | — (Positive) | All 8 runs complete — engine stability is fully consistent across worlds |
| F2 | High | dungeon_crawl: 94–97% attrition by tick 100; only 1–2 survivors; unplayable |
| F3 | Medium | wilderness_survival: near-extinction; 0 buildings makes service-requirement pipeline inert |
| F4 | — (Positive) | urban_political: `town_return` + `harvesting` emerge; best-functioning world config |
| F5 | Low | World ID not recorded in run_manifest.json; run attribution requires external tracking |

---

## Recommended Follow-Up

**P1 — Use urban_political as canonical audit world for D04 and future D05 re-run**
sandbox_world produces only hunger cycling. urban_political produces `town_return`, `harvesting`, and `combat_engage` — enough behavioral variety to audit balance and personality differentiation meaningfully.

**P1 — Balance dungeon_crawl entity count or add health regeneration**
32 entities in 4 regions with 1 building is a combat extinction configuration. Reduce initial entity count to 10–12 or add health regeneration mechanics to give the dungeon crawl world a functional lifecycle.

**P1 — Add at least one building to wilderness_survival**
0 buildings means no `near_service` requirement can ever pass. Adding a camp or outpost building would allow the opportunity pipeline to generate service-dependent routes even in the wilderness theme.

**P2 — Add `world_id` to `run_manifest.json`**
Record the world ID used for each run in the manifest so stored artifacts are self-describing.
