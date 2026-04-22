# Phase 7 Pipeline Scope Audit

This document audits the systems invoked by the `AuthoritativeApplyPipeline.refine` method to identify semantic bleed and define ownership boundaries.

## System Classification Table

| System | Role in Pipeline | Classification | Phase Owner (Semantic Closure) |
| :--- | :--- | :--- | :--- |
| **TownResolutionSystem** | Positional healing/recovery | Substrate Orchestration | Phase 8 (Economy) |
| **ShopSystem** | Transaction enforcement | Substrate Orchestration | Phase 8 (Economy) |
| **BlacksmithSystem** | Repair/Crafting enforcement | Substrate Orchestration | Phase 8 (Economy) |
| **WorldDynamicsSystem** | Regional hazards/drains | Substrate Orchestration | Phase 7 (Closure) |
| **BuildingSabotageSystem**| Infrastructure damage | Substrate Orchestration | Phase 7 (Closure) |
| **InteractionSystem** | Channeling/Harvesting loop | **Core Substrate** | Phase 8 (Interactions) |
| **StrategicIntelligence** | Blocker resolution | Semantic Module | Phase 9 (Strategic Depth) |
| **StrategicRedirection** | Stuck/Path remediation | Semantic Module | Phase 9 (Strategic Depth) |
| **MovementSystem** | Step resolution/Routing | **Core Substrate** | Phase 7 (Closure) |
| **EvolutionSystem** | Growth/Milestone checks | Substrate Orchestration | Phase 7 (Closure) |

## Audit Findings

### 1. Semantic Bleed
- **StrategicIntelligenceSystem** and **StrategicRedirectionSystem** are the primary sources of semantic bleed in the pipeline. They currently reside in `src_v2/systems/` rather than `src_v2/engine/`, indicating they are higher-level logic being invoked by the substrate to prevent navigation deadlocks.
- **Action Recommendation**: These systems should be treated as "Mixed-Surface Temporary Dependencies." Phase 7 does NOT own their logic, only their deterministic orchestration within the 6-phase tick.

### 2. Substrate Integrity
- **MovementSystem** and **InteractionSystem** are properly classified as core substrate. Their logic is 100% owned by Phase 7 to ensure intent-based authority.
- The service systems (**Shop**, **Blacksmith**, **Town**) are providing the necessary substrate-level "effect applicators" for intents, but their complex semantic rules (e.g., dynamic prices) are deferred.

## Conclusion
The refinement pipeline is architecturally sound for Phase 7 closure. The inclusion of Strategic modules is a known and bounded dependency for navigational sanity, but their semantic closure is officially deferred to Phase 9.
