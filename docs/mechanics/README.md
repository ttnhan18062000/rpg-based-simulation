---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-08-26
---

# Simulation Mechanics Bible

Welcome to the definitive reference for the RPG Engine's simulation laws. This manual is designed for developers, modders, and curious users who want to understand the exact mathematical and logical frameworks that drive the world.

## Purpose
Unlike the technical documentation in `engine/` or `core/`, which focuses on "how the code is structured," this manual focuses on **"how the simulation functions."** 

Every formula documented here is verified for **Bit-Identical Parity** with the source code. If a formula in this manual differs from the engine's behavior, it is considered a critical documentation bug.

---

## Table of Contents

### [01: Entity Anatomy](01_entity_anatomy.md)
The biological and physical foundation of all actors.
*   Core Attributes (STR, AGI, VIT, etc.)
*   Derived Combat Stats
*   Biological Pressures (Hunger, Sleep, Stamina)
*   Progression & XP Scaling

### [02: Combat Laws](02_combat_laws.md)
The deterministic math of battle.
*   The Damage Formula
*   Tactical Modifiers (High Ground, Flanking, Cover)
*   Durability Decay
*   Victory Outcomes (Rewards, Rebirth, Permadeath)

### [03: Economic Laws](03_economic_laws.md)
The cycle of wealth and resources.
*   Atomic Conservation Law
*   Harvesting & Resource Nodes
*   Trade & Market Liquidity
*   Crafting & Industry

### [04: Strategic Cognition](04_strategic_cognition.md)
The mental layer of the simulation.
*   Goal Hierarchy & Prioritization
*   Interruption Resistance
*   Knowledge Management (Leads & Blockers)
*   Perception & Salience

### [05: World Evolution](05_world_evolution.md)
The macro-scale laws of the environment.
*   The Passage of Time (Tick-to-Hour-to-Day)
*   Regional Trauma & Hazards
*   Ecology & Replenishment
*   Calamities & World Threats

### [06: Worldbuilding Foundation](06_worldbuilding_foundation.md)
The structural laws of data-driven setup.
*   Declarative World Topology
*   Regional Boundaries & Sovereignty
*   Entity & Resource Distribution
*   Integrity Validation Laws

---

## Sub-Contract Index

The following companion docs extend the Mechanics Bible chapters with formula depth, edge cases, source-module pointers, and regression test references. They are siblings to the chapter files (no subdirectory). Each sub-contract follows the logic-contract template: Purpose, RPG Meaning, Inputs, Core Rules, Formula/Decision Logic, Lifecycle, Mutation Rules, Edge Cases, Examples, Source Areas, Regression Tests, Extension Rules.

| Sub-Contract | Extends | Covers |
|---|---|---|
| [`resource_conservation_contract.md`](resource_conservation_contract.md) | Chapter 03 | Atomic law 4-gate sequence, all 13 failure codes, loot vs regular node, home storage, crafting atomicity, market pricing, concurrent reservation |
| [`adventure_routing_contract.md`](adventure_routing_contract.md) | Chapter 04 | 13 RouteFamily values, opportunity inputs, blocker handling, scoring formula, personality bias, candidate cap, fallback guarantee, ObjectiveIntentResolver |
| [`damage_formula_contract.md`](damage_formula_contract.md) | Chapter 02 | Fractional armor mitigation formula, 7 tactical modifiers in exact application order, durability decay, wound infliction (25% source-authoritative), AoE splash, kill rewards |
| [`attribute_progression_contract.md`](attribute_progression_contract.md) | Chapter 01 | XP threshold formula, level-up execution, +5 AP per level, skill unlocks, 6-phase stat recalc order, skill scaling by type, breakthrough bonus application |

---

## Compliance Status

Chapters 01–04 and 06 are **Certified Level 1 (Authoritative)** as of 2026-06-27. Chapter 05 is **Partially Verified** — structural mechanics confirmed, 2 numeric constants unverified against source (resource respawn interval, trauma delta per death). See `06_worldbuilding_foundation.md §Compliance Status` for the per-chapter table.

Sub-contracts are **Authoritative (P1)** as of 2026-06-13 and are verified against source code. They do not replace chapters — they extend them.
