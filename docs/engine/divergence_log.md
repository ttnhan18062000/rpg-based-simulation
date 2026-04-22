# `src_v2` Divergence Log

This document is the canonical record of intentional behavior shifts in `src_v2` compared to original `src`. Every divergence listed here must have a rationale and be classified according to the `src_v2_principle.md` standards.

## 1. Divergence Summary Table

| Subsystem | Feature | Rationale Class | Status |
| :--- | :--- | :--- | :--- |
| **Grid Engine** | Strict Channeling | **Bug Fix** | RATIFIED |
| **State Layer** | Lowercase Registry Keys | **Lifecycle Truth** | RATIFIED |
| **Interaction** | Immediate Completion | **Contract Hardening** | RATIFIED |
| **Town Loop** | Simplified Recipe Costs | **Intentional Change** | PHASE-LIMITED |
| **AI/Strategic** | Proactive Redirection | **Contract Hardening** | RATIFIED |
| **Tactical** | Priority-Based Targeting | **Contract Hardening** | RATIFIED |
| **Tactical** | 20% Retreat Threshold | **Intentional Change** | RATIFIED |
| **Combat** | Omitted Variance/Evasion | **Substrate Clarity** | PHASE-LIMITED |

---

## 2. Detailed Records

### 2.1 Strict Channeling Enforcement
- **Subsystem**: Grid / Interaction
- **Old Behavior**: Legacy engine allowed "instant-harvest" bugs under specific tick conditions or race timings where the channeled duration was not strictly enforced before update application.
- **New Behavior**: `InteractionSystem.enforce` strictly verifies that `progress >= duration` before adding items to inventory. Aborts occur if the entity moves or interacts with another target.
- **Rationale**: **Bug Fix**. Prevents exploitation of timing bugs and ensures the "Channeling Law" is absolute.
- **Verification**: `tests_v2/parity/test_resource_interaction_parity.py`

### 2.2 Lowercase Registry Keys
- **Subsystem**: Core / State
- **Old Behavior**: Item and resource registry keys used inconsistent casing (e.g., `Iron_Ore`, `iron_ore`, `IRON_ORE`).
- **New Behavior**: All keys are normalized to lowercase during registry loading and state serialization.
- **Rationale**: **Lifecycle Truth Fix**. Stabilizes state hashing and prevents "ghost" items caused by case-sensitivity drit.
- **Verification**: `tests_v2/unit/test_registry_identity_integrity.py`

### 2.3 Immediate Interaction Completion (Tick 0)
- **Subsystem**: Interaction / Inventory
- **Old Behavior**: Interaction completion and item addition often lagged by 1 tick (reported in Tick N+1).
- **New Behavior**: Completion is resolved in the same tick (`Tick 0`) the threshold is reached. Inventory updates are immediately visible to the AI in the same resolution phase.
- **Rationale**: **Contract Hardening**. Synchronizes physical completion with logical state change, simplifying AI reasoning.
- **Verification**: `docs/engine/supported_progression_surface_phase5.md`

### 2.4 Simplified Recipe Costs (Phase 5)
- **Subsystem**: Town Loop / Blacksmith
- **Old Behavior**: `steel_sword` required 2 `iron_ore` and specific auxiliary materials.
- **New Behavior**: `steel_sword` cost simplified to 1 `iron_ore`.
- **Rationale**: **Intentional Gameplay Change**. Simplified specifically for Phase 5 single-loop loop-integrity proofs.
- **Verification**: `docs/engine/phase5_exit_support_boundary.md`
- **Note**: This divergence is restricted to the Phase 5/6 baseline scenarios and may be removed in later Phases.

### 2.5 Proactive Strategic Redirection
- **Subsystem**: AI / Strategic
- **Old Behavior**: AI projects reacted to inventory changes in the next tick.
- **New Behavior**: `StrategicRedirectionSystem` detects inventory resolution and pivots project state within the same resolution phase.
- **Rationale**: **Contract Hardening**. Improves AI effectiveness and ensures the simulation doesn't "waste" a tick on now-obsolete goals.
- **Verification**: `docs/engine/phase5_resource_intelligence_support.md`

### 2.6 Priority-Based Tactical Targeting
- **Subsystem**: Tactical AI
- **Old Behavior**: Nearest enemy was always selected.
- **New Behavior**: Deterministic priority chain: `Lowest HP` > `Closest Distance` > `Lowest Entity ID`.
- **Rationale**: **Contract Hardening**. Prevents target oscillation and improves AI effectiveness in focused firing.
- **Verification**: `tests_v2/parity/test_tactical_parity.py`

### 2.7 20% Retreat Threshold
- **Subsystem**: Tactical AI
- **Old Behavior**: Entities retreated at 25% HP.
- **New Behavior**: Entities retreat at 20% HP.
- **Rationale**: **Intentional Gameplay Change**. Aligns with V2's more aggressive hero-bias scenarios.
- **Verification**: `tests_v2/parity/test_tactical_parity.py`

### 2.8 Omitted Combat Variance/Evasion
- **Subsystem**: Combat Resolution
- **Old Behavior**: Combat included evasion checks and ~10% damage variance.
- **New Behavior**: Combat resolution is currently 100% deterministic (no variance, no evasion).
- **Rationale**: **Substrate Clarity**. Ensuring the base damage resolution is bit-identical and stable before layering stochastic noise.
- **Verification**: `tests_v2/parity/test_combat_parity.py`

---
*Last updated: 2026-04-22 as part of Phase 8 Milestone 5.*
