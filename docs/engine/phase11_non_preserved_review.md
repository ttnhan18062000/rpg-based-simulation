# Phase 11 Non-Preserved Review

This document contains the explicit ratification review for all rows labeled as **DIVERGENT**, **UNSUPPORTED**, or **RETIRED**.

## 1. Intentional Divergences (DIVERGENT)

| ID | Item | Old Behavior | New Behavior | Rationale | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-012** | Melee Legality | Simple range check | Engagement-reg aware | Hardened disengagement/OA rules. | RATIFIED |
| **LEG-RPG-013** | Ranged Legality | Range only | Explicit LoS check | V2 requires true spatial truth. | RATIFIED |
| **LEG-RPG-014** | AoE Legality | Center/Radius | Unified interaction | Architectural consolidation. | RATIFIED |
| **LEG-RPG-036** | Project continuity | Vague margin | Explicit model | Boundedness enforcement. | RATIFIED |
| **LEG-RPG-039** | Lead retention | Unbounded | Profile-capped | Boundedness enforcement. | RATIFIED |
| **LEG-RPG-041** | Detour suggestions | Greedy depth | Bounded breadth | Performance predictability. | RATIFIED |
| **LEG-RPG-107** | Detour limits | Recursive depth | Explicit bounds | Stack safety and predictability. | RATIFIED |
| **LEG-RPG-110** | Profile-capped intake | First-in | Priority-weighted | Resource optimization. | RATIFIED |
| **LEG-RPG-155** | Action Convergence | Simple state | Intent semantic modes | Deterministic loop integrity. | RATIFIED |

## 2. Unsupported Scope (UNSUPPORTED)

| ID | Item | Rationale | Constraint | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-054** | Turning points | Deferred to post-transition. | Not available in V2. | RATIFIED |
| **LEG-RPG-058** | Territory ownership | Deferred to Phase 12+. | Not available in V2. | RATIFIED |
| **LEG-RPG-059** | Class choice gear | Deferred to Phase 12+. | Not available in V2. | RATIFIED |
| **LEG-RPG-061** | Combat rewards (XP) | Pending gameplay overhaul. | Not available in V2. | RATIFIED |
| **LEG-RPG-158** | Flanking / Backstab | Complex bonus logic deferred. | Basic flanking supported. | RATIFIED |

## 3. Retired Scope (RETIRED)

| ID | Item | Retirement Reason | Replaced By | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-021** | Tactical choice | Absorbed into LegalityService. | `LegalityService` invariants. | RATIFIED |
| **LEG-RPG-031** | Guild visits | Merged into Strategic Leads. | `LEG-RPG-164` (Strategic Lead Emission). | RATIFIED |
| **LEG-RPG-033** | Building gameplay | Absorbed into InteractionSystem. | `InteractionSystem` orchestration. | RATIFIED |
| **LEG-SYS-003** | Broker Fallback | V2 uses in-process queue. | `V2EngineManager` tick listeners. | RATIFIED |

## 4. Review Observations

- **Rationale Completeness**: All DIVERGENT rows have explicit rationale in the `Note` column of the ledger.
- **Omission Strategy**: UNSUPPORTED rows are explicitly identified as deferred to prevent accidental assumption of parity in Phase 12.
- **Retirement Integrity**: All RETIRED rows represent architectural consolidation rather than lost functionality.

---
**Ratification Status**: OPEN
**Baseline Version**: 2026-04-24.1
