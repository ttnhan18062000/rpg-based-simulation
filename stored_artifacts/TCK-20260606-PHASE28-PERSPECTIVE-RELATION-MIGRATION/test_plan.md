---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260606-PHASE28-PERSPECTIVE-RELATION-MIGRATION
artifact_type: test_plan
tags: [phase28, perspective, relation, migration]
---

# Phase 28 Test Plan

We will verify both target classification and legacy fallback using integration tests.

## Test Cases

### 1. Target Classification and Perspective Checks
- Attacker: `hero_guild` faction entity.
- Target: `goblin_warband` faction entity (should be targeted as `enemy`).
- Target: `merchant_league` faction entity (should NOT be targeted as `enemy`).

### 2. Contextual Threat Checks
- Attacker: `hero_guild` faction entity.
- Target: `wild_beast_pack` faction entity.
- Context:
  - Combat engaged or distance <= 5.0: target classified as `enemy` / `threat` (hostile).
  - Distance > 5.0 (and not combat engaged): target classified as `neutral` (not hostile).

### 3. Legacy Fallbacks
- Attacker: `villagers` faction entity.
- Target: `monsters` faction entity.
- No perspective/relationship data exists.
- Target should fall back to legacy hostility check (hostile since `monsters` is a MONSTER_HORDE faction).
- Log output should emit the debug warning `"Falling back to legacy hostility semantics"`.
