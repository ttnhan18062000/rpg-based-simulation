# Phase 11 Non-Preserved-Scope Baseline

This document summarizes the ratified non-equivalence truth as of Phase 11.

## 1. Summary Table

| Category | Divergent Rows | Unsupported Rows | Retired Rows |
| :--- | :--- | :--- | :--- |
| **RPG Core** | 12 | 18 | 3 |
| **System Compatibility** | 0 | 0 | 1 |
| **Total** | 12 | 18 | 4 |

## 2. Intentional Divergences (Summary)
V2 deviates from legacy in several key areas to enforce **Boundedness** and **Authoritative Truth**:
- **Legality Enforcement**: Stricter LoS and Engagement rules.
- **Cognitive Boundedness**: Profile-capped lead intake, detour depth, and attention limits.
- **Deterministic Loop**: Intent-mode based action convergence.

## 3. Unsupported Scope (Summary)
The following legacy systems are explicitly **EXCLUDED** from the replacement claim:
- **Turning Points**: Post-transition gameplay feature.
- **Complex Progression**: XP rewards, class-specific gear breakthroughs, and territory ownership.
- **Legacy UI**: Handled via new API/WS contracts.

## 4. Retired Scope (Summary)
The following architectural artifacts are **REMOVED** and replaced by singular engine systems:
- **Geometry Exploits**: Replaced by LegalityService invariants.
- **External Broker PUB/SUB**: Replaced by in-process tick notification.
- **Scattered Building Logic**: Replaced by InteractionSystem orchestration.

---
**Ratification Status**: PROVISIONAL (Non-Preserved Surface Closed)
**Audit Date**: 2026-04-24
