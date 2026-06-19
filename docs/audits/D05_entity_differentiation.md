---
audit_id: D05
title: Entity Differentiation
status: done
date: 2026-06-19
ticket: TCK-20260619-AUDIT-D05-ENTITY-DIFF
layer: simulation
priority: P1
tags: [entity-differentiation, personality, class, role, behavioral-arcs, audit-blocker]
---

# D05 — Entity Differentiation

## Dimension Profile

| Field | Value |
|---|---|
| Audit ID | D05 |
| Method | run-sim + code-read |
| Priority | 8 |
| Scope | `src/domains/adventure/scoring.py`, `src/worldbuilding/compiler.py`, `data/worlds/sandbox_world/`, `data/content/` |
| Seeds | 42, 137 |
| Ticks | 400 each (covers 200-tick dead zone + 200 ticks of active behavior) |
| Observability | LIGHT + direct state inspection at tick 0 |

## What this dimension answers

Do entity role (HERO/MONSTER/CITIZEN/WORKER/GUARD/SHOPKEEPER) and personality traits (bravery, greed, industry, sociability — OCEAN-derived) produce observably different behavioral arcs across entities and seeds?

## Related Dimensions

| Dimension | Relationship |
|---|---|
| D01 (RPG Feature Impact) | Flagged "Personality → Long-Run Behavior Calibration `[PARTIAL]`" — D05 confirms and pinpoints why |
| D06 (Long-Run Health) | F1 (survival-only routes) means D05 can only assess differentiation within survival behavior |
| D03 (Behavioral Emergence) | RC1/RC2/RC3 fixed before this run; behavioral activity confirmed from tick ~201 |

---

## Investigation Method

Two complementary approaches:

1. **Direct state inspection**: built the world for seeds 42 and 137 using `WorldCompiler.compile()` at tick 0, read every entity's `identity.personality`, `identity.class_id`, `identity.role`, and `position` directly from the `AuthoritativeState`.

2. **Run-sim observation**: 400-tick runs, extracted per-entity project kind histories from `simulation_events.jsonl` and correlated against role/position.

---

## Entity Population — Seeds 42 and 137

Both seeds produce an identical population structure:

| Entities | Role | Role ID | class_id | bravery | greed | industry | sociability | spawn_region |
|---|---|---|---|---|---|---|---|---|
| 1–15 | CITIZEN | 3 | NOVICE | 0.0 | 0.0 | 0.0 | 0.0 | town_center |
| 16–20 | MONSTER | 2 | NOVICE | 0.0 | 0.0 | 0.0 | 0.0 | (distant) |

**Absent roles**: HERO (0), SHOPKEEPER (1), WORKER (4), GUARD (5) — none appear in sandbox_world.

---

## Run Results — Per-Entity Behavior (seed 42, ticks 201–400)

| Entity | Role | Active ticks | Project kinds observed |
|---|---|---|---|
| 1–5, 7–8, 10–13, 15 | CITIZEN | 201–270 | hunger × 2, resolve_blocker × 1 |
| 6, 9, 14 | CITIZEN | 201–340 | hunger × 8 (no resolve_blocker) |
| 16 | MONSTER | tick 5 only | combat_retreat (then dies) |
| 17, 18 | MONSTER | ticks 3–4 only | recover (then die) |
| 19, 20 | MONSTER | silent | dead from spawn |

Seed 137 shows the same structural split: some CITIZENs cycle hunger + resolve_blocker, others cycle hunger only. The MONSTER subset all die in early combat. The entity IDs in each group differ between seeds (entity 6/9/14 in seed 42; entities 1/5/6/7/8/9 in seed 137), ruling out a fixed per-entity property as the cause.

---

## Scoring Formula Analysis

`AdventureRouteScorer.score()` computes:

```
score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
```

With all traits at 0.0:

| Derived value | Formula | Result for all entities |
|---|---|---|
| `caution` | `1.0 - bravery` | **1.0** (maximum caution) |
| `personality_bias` for RECOVER | `caution × 0.25` | **0.25** |
| `personality_bias` for all other families | `greed/curiosity/industry/sociability × 0.25` | **0.0** |

Every entity receives identical scoring weights. The only source of score variation between entities is `urgency` (from `entity.self_model.needs.active_needs`), `benefit` and `risk` (from opportunity properties), and `confidence` (from opportunity confidence field). None of these are personality-driven.

---

## Findings

### F1 — Personality Traits Not Initialized: All Zero Across All Entities

**Severity: Critical**

`WorldCompiler.compile()` produces `PersonalityComponent(greed=0.0, bravery=0.0, sociability=0.0, industry=0.0)` for every entity in both seeds. The `PersonalityComponent` dataclass is instantiated with zero defaults and never seeded with randomized values during world compilation.

Consequence: all entities receive maximum caution (`1.0`) and zero greed, industry, sociability from the scorer's derived values. Every entity is scored identically for every route family. The personality bias term in the scoring formula contributes nothing to differentiation — it applies a flat +0.25 to RECOVER routes for all entities uniformly.

The OCEAN personality system (`TCK-20260407-PHASE1-PERSONALITY`) is implemented and the scoring formula correctly uses it — but the initialization pipeline never seeds it. World compilation must call a personality randomization function (seeded by entity ID + world seed) to populate non-zero trait values.

**Evidence**: Direct `AuthoritativeState` inspection at tick 0 for seeds 42 and 137.

---

### F2 — Class System Not Populating: All Entities Are NOVICE

**Severity: High**

Every entity — CITIZEN and MONSTER alike — has `class_id = NOVICE`. No warrior, mage, rogue, ranger, or any other class is assigned. The class field exists on `IdentityComponent` and likely drives attribute differentiation (STR, INT, DEX, etc.), but the world compiler never assigns non-NOVICE classes.

This compounds F1: even if personality traits were seeded, class-based attribute differences (e.g. INT driving curiosity in the scorer) would still be absent.

---

### F3 — No HERO Role Entities in sandbox_world

**Severity: High**

The six entity roles are: HERO (0), SHOPKEEPER (1), MONSTER (2), CITIZEN (3), WORKER (4), GUARD (5). Sandbox_world spawns only CITIZEN (15 entities) and MONSTER (5 entities). The HERO role — the intended protagonist class — is absent.

`AdventureDecisionPhase` processes all `alive + active` entities regardless of role (the docstring says "heroes" but the filter at `phase.py:43` is `combat.alive and lifecycle.active`). This means CITIZEN entities run the adventure decision pipeline — conceptually wrong, and producing uniform survival behavior rather than hero-class goal pursuit.

---

### F4 — Observed Behavioral Variation is Positional, Not Personality-Driven

**Severity: Informational**

The `resolve_blocker` project pattern varies between entities (some get it, others do not) and varies between seeds (different entities in each group). After eliminating personality as the cause (F1), the remaining explanation is spatial: entities positioned within 5.0 units of a functional building pass the `near_service` requirement check (RC2 fix) and never generate a `too_far_from_service` blocker. Entities further from buildings fail it, generate a blocker, and spawn a `resolve_blocker` detour project.

This is spatial variation, not behavioral differentiation driven by character design.

---

### F5 — Role-Based Mortality Differentiation (Structural, Not Behavioral)

**Severity: Low / Informational**

MONSTERs (entities 16–20) die in early combat (ticks 3–15) in both seeds due to their distant spawn position and combat adjacency. CITIZENs survive. This IS a form of role differentiation — but it is mortality-based (who lives vs who dies) rather than behavioral-arc-based (how different roles pursue different goals while alive). There is no observable behavioral divergence among the entities that survive.

---

## Key Findings Summary

| Finding | Severity | Description |
|---|---|---|
| F1 | Critical | All personality traits 0.0 at spawn — world compiler never seeds `PersonalityComponent` |
| F2 | High | All entities are `class_id = NOVICE` — class system not populating at world build |
| F3 | High | No HERO role in sandbox_world — adventure pipeline runs on CITIZENs |
| F4 | Info | Behavioral variation (resolve_blocker vs none) is positional, not personality-driven |
| F5 | Info | MONSTER role produces early mortality; CITIZENs survive — mortality differentiation only |

**Net result**: Zero personality-driven or class-driven behavioral differentiation is observable in the current simulation. All CITIZENs are functionally identical. The system architecture (OCEAN traits, class attributes, scoring formula) is correctly designed — the gap is entirely in initialization.

---

## Recommended Follow-Up

**P0 — Seed `PersonalityComponent` during world compilation**
`WorldCompiler.compile()` (or its entity-spawning subsystem) must call a personality initialization function that randomizes traits using the entity's ID and world seed. Suggested approach: use the existing `DeterministicRNG` with a per-entity sub-seed to assign values in [0.0, 1.0] to bravery, greed, industry, sociability. This is the single highest-leverage fix — it unlocks observable differentiation across all entities immediately.

**P0 — Assign non-NOVICE `class_id` values via spawn tables**
`data/content/spawn_tables.yaml` (currently only defines MONSTER/WORKER weights) should include class assignments per entity kind. `WorldCompiler` should read these during entity spawn.

**P1 — Add HERO role entities to sandbox_world**
`data/worlds/sandbox_world/world.yaml` should include at least 2–3 entities with `role = HERO` so the adventure decision pipeline has intended protagonists. This also enables testing the full strategic cognition chain (D19 gap).

**P2 — Add per-entity personality observability**
LIGHT observability mode does not surface per-entity personality traits or scoring weights. A lightweight entity snapshot (role, class, personality vector, active_project_kind) at tick N would make D05-type analysis routine rather than requiring direct state introspection. This connects to D15 findings.
