---
status: active
layer: engine
authority: P1
audience: developer
---

# Governance Logic: Authoritative Implementation

## 1. Authoritative Flow
Governance logic is executed in **Phase 12: Town Governance** of the `AuthoritativeApplyPipeline`.

### 1.1 TownResolutionSystem
The `TownResolutionSystem` is the primary resolver for:
- **Tax Extraction**: Aggregates gold from entity inventories and building production.
- **Vault Deposit**: Updates `StateUpdate.resource_updates` with aggregated faction gold.
- **Maintenance Deduction**: Deducts gold from the vault; if insufficient, flags buildings as non-functional.

### 1.2 WorldDynamicsSystem
The `WorldDynamicsSystem` handles the territorial aspect:
- **Influence Accumulation**: Increments `influence_delta` in `WorldUpdate` based on tick events (deaths).
- **Ownership Hysteresis**: Prevents rapid flipping by requiring a 20-point buffer to regain control once lost.

## 2. Resource Conservation
All governance-driven gold transfers must follow the **Conservation Law (RPG-AUTH-003)**:
- Total Gold in World = Sum(Entity Gold) + Sum(Building Gold) + Sum(Faction Vaults).
- Any tax extracted from an entity MUST be added to a vault or building update.

## 3. Degradation Laws
Governance logic adapts to `ResourceGovernor` modes:
- **NORMAL**: Full taxation and maintenance logic.
- **CONSTRAINED**: Simplified taxation (flat rates).
- **DEGRADED**: No maintenance checks; all buildings functional.
- **SURVIVAL**: Governance phase skipped entirely.
