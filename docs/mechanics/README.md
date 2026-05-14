# Simulation Mechanics Bible (V2)

Welcome to the definitive reference for the V2 RPG Engine's simulation laws. This manual is designed for developers, modders, and curious users who want to understand the exact mathematical and logical frameworks that drive the world.

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

---

## 📜 Compliance Status
All chapters are currently **Certified Level 1 (Authoritative)**. This means the documentation matches the current source code implementation as of Tick 0 of the V2 Engine deployment.
