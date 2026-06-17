---
status: historical
layer: engine
authority: P2
audience: developer
---

# Authoritative Replacement Ledger Schema

This document defines the canonical schema for the **Authoritative Replacement Ledger**. Every legacy behavior or system contract must be represented as a row in this ledger to track its status, divergence, and implementation phase.

## 1. Column Definitions

| Column | Description |
| :--- | :--- |
| **ID** | Stable identifier. Format: `LEG-{AREA}-{NUM}` (e.g., `LEG-RPG-001`). |
| **Area** | Subsystem grouping for traceability (e.g., `CORE-RESOURCE`, `SYS-CLI`). |
| **Atomic Item**| The specific behavior or contract name. |
| **Legacy Source**| File path and line range in the original `src/`. |
| **Legacy Test** | Test module or function in the original `tests/`. |
| **V2 Source** | File path and line range in `src/`. |
| **V2 Test** | Test file path or function in `tests/`. |
| **Proof Artifact**| Link to Proof Bundle or Parity Oracle. |
| **Maturity** | `IMPLEMENTED`, `TESTED`, `PROOF-BACKED`, `SUPPORTED`. |
| **Status** | `SUPPORTED`, `DIVERGENT`, `UNSUPPORTED`, `RETIRED`. |
| **Note**| Divergence rationale or classification note. |
| **Proof Path** | Assigned path from [Proof-Path Taxonomy](../../engine/proof_path_taxonomy.md). |
| **Target Phase** | High-level phase for final closure (Phases 7-10). |
| **Dependency** | Cross-phase or substrate blockers. |
| **Closure Condition**| Specific requirement for formal "DONE" status. |

## 2. Granularity Guidance

The "Atomic Item" must represent a single, verifiable contract or rule. 

### Avoid "Too Broad"
- ❌ "Harvesting Logic" (Too many disparate rules).
- ❌ "Combat System" (An entire milestone).

### Avoid "Too Fine"
- ❌ "Line 142 if check" (Too brittle).
- ❌ "Variable naming in loop" (Implementation detail).

### Precise (Recommended)
- ✅ "Harvesting Channeling Completion Rule" (Specific contract).
- ✅ "Inventory Weight Capacity Enforcement" (Specific rule).
- ✅ "CLI `--seed` Parameter Support" (Specific interface item).

## 3. Maturity Dimensions

To maintain "Baseline Honesty," V2 implementation status is split into four distinct dimensions:

- **IMPLEMENTED**: Code exists in `src` that claims to handle the item. No verification assumed.
- **TESTED**: Direct unit or integration tests exist in `tests` for the item.
- **PROOF-BACKED**: The item is verified via a **Parity Oracle** or **Contract Test** against the legacy baseline.
- **SUPPORTED**: The item is officially declared as "Official" or "Supported" in consumer-facing docs (e.g., `support_matrix.md`).

> [!CAUTION]
> A row can be **IMPLEMENTED** but **UNSUPPORTED**. This often indicates "Implementation Drift" or partial recovery.

## 4. Classification Definitions

- **SUPPORTED**: Bit-identical or semantic-equivalent proof exists in `src`.
- **DIVERGENT**: Behavior exists but intentionally differs from legacy (rationalized).
- **UNSUPPORTED**: Behavior is present in legacy code but will not be recovered.
- **RETIRED**: Behavior is obsolete or replaced by a fundamentally different design (e.g., AOA transitions).
