# Calamities (World Boss) System - Phase 2 & 3 Expansion

This document outlines the design and implementation details for the Calamity system, restoring and enhancing Phase 2 (World Evolution) and Phase 3 (Town Resilience) of Epic 19.

## Overview
Calamities are "World Boss" entities that appear periodically, posing a global threat to the simulation. They introduce high-tier progression, legendary rewards, and regional environmental effects.

## Core Mechanics

### 1. Entity Role & Scaling
- **WORLD_BOSS Role**: A new `EntityRole` specifically for Calamities.
- **Stat Scaling**: Bosses have a base `stat_multiplier` (5x-6x) applied on top of global world difficulty scaling.
- **Legendary Rarity**: New item rarity `LEGENDARY` (4) for boss equipment and materials.

### 2. Spawning & Logic
- **Spawn Interval**: A boss spawns every 5,000 ticks if none are currently active.
- **AI Behavior**: Non-leashing roaming behavior with specialized personality traits (e.g., `SIEGE_MASTER`, `VENGEFUL`).
- **Historical Memory**: Bosses "remember" past encounters, gaining buffs against classes that have previously defeated them.

### 3. Regional Impact (Calamity Aura)
- Calamities emit a regional aura that:
  - Debuffs Heroes (-10% Evasion/SPD).
  - Buffs Minions of the same faction (+10% ATK).

### 4. Progression & Rewards
- **Fame System**: A new hero stat (`fame`) earned by completing boss bounties.
- **Bounty Quests**: New `BOUNTY` quest type generated when a boss spawns.
- **Hero Titles**: Slain bosses grant unique titles (e.g., "Slayer of Gorath") with permanent stat bonuses.
- **Tier 3 (Transcendence) Classes**:
  - `WARLORD`, `STORM_CALLER`, `GHOST_STALKER`, `NIGHTSHADE`.
  - **Requirements**: Level 20 + 100 Fame + `Calamity Remnant` (Legendary material).

## Implementation Files
- **Enums**: `src/core/enums.py` (`WORLD_BOSS`, `LEGENDARY`, `Domain.CALAMITY`).
- **Models**: `src/core/models.py` (`fame`, `titles`, `is_world_boss`).
- **Data**: `src/core/calamities.py` (Boss templates).
- **Items**: `src/core/items.py` (Legendary gear/materials).
- **Systems**: `src/systems/generator.py` (`spawn_calamity`).
- **Engine**: `src/engine/world_loop.py` (Spawn checks, auras, events).
- **Actions**: `src/actions/combat.py` (Rewards, fame, titles).

## Verification Plan
- **Automated Tests**: `tests/test_calamity_system.py` covers spawning, bounties, and kill rewards.
- **Documentation**: Updates to `docs/combat_and_progression.md` and `docs/world_evolution_and_resilience.md`.
