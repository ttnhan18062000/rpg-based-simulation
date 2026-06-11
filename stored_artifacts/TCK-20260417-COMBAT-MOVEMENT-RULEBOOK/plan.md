---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260417-COMBAT-MOVEMENT-RULEBOOK
artifact_type: plan
tags: [combat, movement, rulebook]
---

# Implementation Plan: Combat and Movement Milestone 1

## Goal
Freeze the rulebook and refactor engine time.

## Proposed Changes
### Rulebook Definition
- Create `docs/combat/combat_movement_rulebook_m1.md`.
- Create `docs/combat/combat_movement_m1_test_matrix.md`.

### Rule Contract (Code)
- Create a centralized `Rulebook` or `SpatialContract` service/module to hold authoritative legality logic.
- Refactor `CombatAction` and `MoveAction` to use this new contract.

### Engine Loop Refactor
- Modify `WorldLoop` or specific phases to clearly distinguish between world-time advancement and action scheduling.

## Manual Verification
- Run the simulation in headless mode and verify tick logs.
- Run the Arena/E2E suite (if available) to ensure basic combat still functions.
