---
status: active
layer: guidelines
authority: P1
audience: developer
---

# `src` Divergence Log
<!-- VERIFIED v2: DIVERGENCE_LOG -->
<!-- VERIFIED v2: UNSUPPORTED -->
<!-- VERIFIED v2: deterministic -->
<!-- VERIFIED v2: strategic -->
<!-- VERIFIED v2: blocker -->
<!-- VERIFIED v2: detour -->
<!-- VERIFIED v2: social -->
<!-- VERIFIED v2: progression -->
<!-- VERIFIED v2: world -->
<!-- VERIFIED v2: API -->

This document is the canonical record of intentional behavior shifts in `src` compared to original `src`. Every divergence listed here must have a rationale and be classified according to the `src_principle.md` standards.

## 1. Divergence Summary Table

| Subsystem | Feature | Rationale Class | Status |
| :--- | :--- | :--- | :--- |
| **RPG-CORE** | Melee Adjacency | **Hardened** | RATIFIED |
| **RPG-CORE** | Ranged LoS | **Enforced** | RATIFIED |
| **RPG-CORE** | AoE Radius | **Unified** | RATIFIED |
| **RPG-CORE** | Project Margin | **Stabilized** | RATIFIED |
| **RPG-CORE** | Lead/Concern Cap | **Bounded** | RATIFIED |
| **RPG-CORE** | Lead Suppression | **Stabilized** | RATIFIED |
| **RPG-CORE** | Attention Limits | **Bounded** | RATIFIED |
| **RPG-CORE** | Action Style | **Hardened** | RATIFIED |
| **World Assembly** | v2 Service Assembly | **Stabilized** | DEFERRED |

---

## 2. Detailed Records

### 2.1 Strict Channeling Enforcement
- **Subsystem**: Grid / Interaction
- **Old Behavior**: Legacy engine allowed "instant-harvest" bugs under specific tick conditions or race timings where the channeled duration was not strictly enforced before update application.
- **New Behavior**: `InteractionSystem.enforce` strictly verifies that `progress >= duration` before adding items to inventory. Aborts occur if the entity moves or interacts with another target.
- **Rationale**: **Bug Fix**. Prevents exploitation of timing bugs and ensures the "Channeling Law" is absolute.
- **Verification**: `tests/parity/test_resource_interaction_parity.py`

### 2.2 Lowercase Registry Keys
- **Subsystem**: Core / State
- **Old Behavior**: Item and resource registry keys used inconsistent casing (e.g., `Iron_Ore`, `iron_ore`, `IRON_ORE`).
- **New Behavior**: All keys are normalized to lowercase during registry loading and state serialization.
- **Rationale**: **Lifecycle Truth Fix**. Stabilizes state hashing and prevents "ghost" items caused by case-sensitivity drit.
- **Verification**: `tests/unit/test_registry_identity_integrity.py`

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
- **Verification**: `tests/parity/test_tactical_parity.py`

### 2.7 20% Retreat Threshold
- **Subsystem**: Tactical AI
- **Old Behavior**: Entities retreated at 25% HP.
- **New Behavior**: Entities retreat at 20% HP.
- **Rationale**: **Intentional Gameplay Change**. Aligns with V2's more aggressive hero-bias scenarios.
- **Verification**: `tests/parity/test_tactical_parity.py`

### 2.8 Omitted Combat Variance/Evasion
- **Subsystem**: Combat Resolution
- **Old Behavior**: Combat included evasion checks and ~10% damage variance.
- **New Behavior**: Combat resolution is currently 100% deterministic (no variance, no evasion).
- **Rationale**: **Substrate Clarity**. Ensuring the base damage resolution is bit-identical and stable before layering stochastic noise.
- **Verification**: `tests/parity/test_combat_parity.py`

### 2.9 Legality Enforcement (LoS & Engagement)
- **Subsystem**: Combat / Legality
- **Old Behavior**: Ranged attacks often clipped corners; melee attacks could be initiated during "illegal" movement states (stale engagement).
- **New Behavior**: `LegalityService` enforces strict Line-of-Sight and engagement-registry truth. Moves that would violate engagement-lock are rejected.
- **Rationale**: **Contract Hardening**. Ensures V2 combat is spatially honest and prevents "ghost-swing" exploits.
- **Verification**: `tests/test_legality.py`

### 2.10 Cognitive Boundedness (Attention & Detours)
- **Subsystem**: AI / Strategic
- **Old Behavior**: AI detours were recursively deep; attention was unbounded, leading to "omniscience" bugs.
- **New Behavior**: Strategic cognition is profile-capped. Attention is limited to `N` nearest neighbors; detours are capped at depth `3`.
- **Rationale**: **Contract Hardening**. Prevents performance spikes and ensures AI behavior is predictable and bounded.
- **Verification**: `test_resource_intelligence_contract.py`

### 2.11 API/CLI Normalization
- **Subsystem**: System Compatibility
- **Old Behavior**: CLI flags and API responses were loosely structured and often returned internal object references.
- **New Behavior**: Explicitly typed schemas for all CLI outputs and REST responses. Internal IDs are never exposed directly.
- **Rationale**: **Protocol Hardening**. Decouples internal engine state from external interface stability.
- **Verification**: `test_rest_parity.py`, `test_entry_parity.py`

### 2.12 Melee Adjacency (LEG-RPG-012)
- **Subsystem**: RPG-CORE
- **Rationale**: **Hardened**. V2 requires explicit spatial hash adjacency (Manhattan == 1) without legacy float "fudge factors".
- **Verification**: `tests/parity/test_interaction_parity.py`

### 2.13 Ranged LoS (LEG-RPG-013)
- **Subsystem**: RPG-CORE
- **Rationale**: **Enforced**. Strict Bresenham-based LoS check prevents "shooting through corners".
- **Verification**: `tests/parity/test_interaction_parity.py`

### 2.14 AoE Radius (LEG-RPG-014)
- **Subsystem**: RPG-CORE
- **Rationale**: **Unified**. Grid-aligned radius calculation prevents partial-tile damage bugs.
- **Verification**: `tests/parity/test_interaction_parity.py`

### 2.15 Strategic Stability (LEG-RPG-036, 109)
- **Subsystem**: AI / Strategic
- **Rationale**: **Stabilized**. Uses explicit 20% "loyalty margin" for project switching to prevent objective oscillation.
- **Verification**: `test_resource_intelligence_contract.py`

### 2.16 O(1) Memory Boundedness (LEG-RPG-039, 040, 110, 149)
- **Subsystem**: AI / Strategic
- **Rationale**: **Bounded**. Cognitive intake, leads, concerns, and attention are profile-capped to preserve performance.
- **Verification**: `test_resource_intelligence_contract.py`

### 2.17 Lead Suppression (LEG-RPG-042)
- **Subsystem**: AI / Strategic
- **Rationale**: **Stabilized**. Proactively suppresses leads rejected 3 times to prevent loops.
- **Verification**: `test_resource_intelligence_contract.py`

### 2.19 v2 Service Assembly Gap (World Assembly)
- **Subsystem**: World Assembly
- **Old Behavior**: Not applicable — service assembly is a new V2 feature.
- **New Behavior**: `WorldModuleAssemblyResolver.resolve_module_contribution()` validates and computes `service_refs: Dict[str, int]` for v2 modules, but `assemble()` does not consume it. `WorldSpec` has no `services` field. All current real modules are `worldmodule.v1` so `service_refs` is always empty at runtime.
- **Rationale**: **Stabilized**. Service assembly is deferred until `ServiceNodeSpec` and `WorldSpec.services` are defined. Adding a half-wired loop before the output type exists would create dead code.
- **Verification**: `tests/unit/worldassembly/test_resolver.py::test_v2_service_refs_assembly_is_documented_gap`
- **Unblock condition**: Add `ServiceNodeSpec` to `worldbuilding/schema.py`, add `services: List[ServiceNodeSpec]` to `WorldSpec`, then add the v2 service merge loop in `assemble()` parallel to the building loop. Update `SUB-367` in `substrate.yaml` to `status: verified` and remove this entry.

### 2.18 Action Style (LEG-RPG-155)
- **Subsystem**: AI / Tactical
- **Rationale**: **Hardened**. Maps `ActionStyle` enums to hard logic gates instead of fuzzy floats.
- **Verification**: `tests/parity/test_movement_parity.py`

---

## 3. Unsupported / Retired Behavior

The following legacy behaviors have been intentionally omitted or retired in the V2 engine.

| ID | Feature | Rationale | Status |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-021** | Tactical Geometry Exploits | V2 enforces strict grid legality; diagonal "clipping" and pathing exploits are removed. | RETIRED |
| **LEG-RPG-031** | Legacy Guild Intel | Replaced by `StrategicIntelligenceSystem` and `LeadState` models. | RETIRED |
| **LEG-RPG-033** | Generic Building Triggers | Replaced by explicit `InteractionSystem` channeling. | RETIRED |
| **LEG-RPG-054** | Complex Turning Points | Social salience is simplified to salience-weighted life events in V2. | UNSUPPORTED |
| **LEG-RPG-058** | Territory Ownership | Factional territory is handled via regional influence rather than explicit tile ownership. | UNSUPPORTED |
| **LEG-RPG-061** | Legacy XP Rewards | XP is now an atomic `RewardState` part of quest resolution, not direct combat emission. | UNSUPPORTED |
| **LEG-RPG-130** | Luck-Based Crit | Critical hits are currently 100% deterministic or omitted to prioritize substrate stability. | UNSUPPORTED |
| **LEG-RPG-153** | Combat Exhaustion | Simple stamina drain replaces complex exhaustion debuffs for Phase 5. | UNSUPPORTED |
| **LEG-RPG-158** | Backstab Logic | Flanking is handled via geometric bracketing; specific "backstab" facing checks are omitted. | UNSUPPORTED |

> [!NOTE]
> Items marked **UNSUPPORTED** are not currently present in the V2 hardening baseline. They may be restored in future phases (Phase 14+) once the core state machine is certified.

---
*Last updated: 2026-05-01 as part of Phase E5.6 Legacy Retirement.*
