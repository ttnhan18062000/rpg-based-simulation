---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 11 Preserved-Surface Baseline

This document summarizes the reconciled preserved replacement truth as of Phase 11.

## 1. Summary Table

| Category | Preserved Rows | Downgraded/Retired | Coverage (%) |
| :--- | :--- | :--- | :--- |
| **System Compatibility** | 11 | 0 | 100% |
| **Strategic Cognition** | 11 | 0 | 100% |
| **Substrate & Lifecycle** | 6 | 0 | 100% |
| **Tactical & Movement** | 8 | 0 | 100% |
| **RPG Core (General)** | 52 | 3 | 94% |

## 2. Preserved Rows (Ratified)

The following rows are confirmed as preserved with explicit evidence:

- **SYS-COMPAT**: LEG-SYS-001, 002, 006, 010, 011, 012, 013, 014, 015, 016, 020.
- **RPG-STRAT**: LEG-RPG-116, 117, 119, 123, 124, 125, 141, 144, 145, 150, 151.
- **RPG-SUBSTRATE**: LEG-RPG-001, 002, 071, 073, 139, 143.
- **RPG-TACTICAL**: LEG-RPG-009, 010, 020, 075, 076, 077, 091, 146.

## 3. Downgraded / Retired Rows (Phase 11 Correction)

The following rows were corrected during the Phase 11 Milestone 2 audit:

| ID | Item | Old Status | New Status | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-021** | Tactical choice | SUPPORTED | RETIRED | Invariant enforced by LegalityService; no standalone feature logic. |
| **LEG-RPG-031** | Guild visits | SUPPORTED | RETIRED | Replaced by `LEG-RPG-164` (Strategic Lead Emission). |
| **LEG-RPG-033** | Building gameplay | SUPPORTED | RETIRED | Covered by `InteractionSystem` orchestration. |

## 4. Remaining Weak-Proof Areas

- **LEG-RPG-018** (Anti-stalemate): Lacks bit-identical parity proof; verified only via cycle-detection behavior.
- **LEG-RPG-152** (Flow Field Far-target): Verified via `test_wind_pillar_navigation.py` which is a high-level integration test; lacks narrow unit-parity proof.

---
**Ratification Status**: PROVISIONAL (Preserved Surface Closed)
**Audit Date**: 2026-04-24
