---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 8 Milestone 2 Audit: Combat Legality & Outcomes

This document maps the Phase 8 combat rows to the current implementation and identifies specific gaps.

## Row Mapping & Gap Analysis

| ID | Atomic Item | Status | Implementation Point | Identified Gaps |
| :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-098** | Engagement Hostility | **PARTIAL** | `LegalityServiceV2.get_engaged_hostiles` | Faction-based initiation rules are not yet formalized as an attack validator. |
| **LEG-RPG-012** | Melee Legality | **PARTIAL** | `LegalityServiceV2.is_adjacent` | Adjacency check exists but is not integrated into a standard melee attack action. |
| **LEG-RPG-013** | Ranged Legality | **MISSING** | N/A | No explicit range-limit or LoS checks for combat interactions. |
| **LEG-RPG-094** | Cover bonus | **MISSING** | N/A | Combat resolution does not account for environmental markers. |
| **LEG-RPG-100** | Target Stickiness | **MISSING** | N/A | (Deferred to Milestone 3) No tactical bias logic yet. |

## Structural Gaps

### 1. Unified Attack Legality
The engine lacks a centralized `verify_attack(attacker, target)` entry point in the `LegalityService`. Actions currently perform ad-hoc checks or rely on simulated outcome assumptions.

### 2. Standard Combat Resolution
`CombatReactionSystem` only handles Opportunity Attacks. Standard melee and ranged attacks have no authoritative resolution logic in `src`.

### 3. Defeat/Kill Semantics
`CombatUpdate` and `ApplyPipeline` do not yet distinguish between "Defeated" (non-lethal/regeneration allowed) and "Killed" (permanent removal). HP dropping to zero simply sets `active=False` without semantic classification.

## Next Action
Implement `LegalityServiceV2.verify_attack` and `CombatReactionSystem.resolve_attack` to close the core combat contract.
