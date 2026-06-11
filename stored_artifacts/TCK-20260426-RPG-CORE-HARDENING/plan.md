---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260426-RPG-CORE-HARDENING
artifact_type: plan
tags: [rpg, core, hardening]
---

# Plan: RPG Core Life-Loop & Arena Hardening

## Goal
Restore authoritative RPG mechanics (rewards, mortality, attrition) and verify them through extended E2E Arena testing.

## Proposed Changes
- src/engine/apply.py: Consolidate corpse spawning, biological decay, and readiness penalties.
- src/engine/combat.py: Implement XP/Gold rewards, Shatter (1.5x), and Exhaustion (0.8x Atk) modifiers.
- src/engine/domain_logic.py: Support multi-entity combat updates and target lookup fallbacks.
- src/certification/scenarios.py: Add scenarios for TACTICAL (High Ground), SOCIAL (Synergy), and PROGRESSION (Loot).

## Verification
- tests/rpg/test_rpg_core_recovery.py: Authoritative micro-tests for all core mechanics.
- E2E Arena Scenarios: Verify emergent behavior in simulated battles.
