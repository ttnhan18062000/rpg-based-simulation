---
status: historical
layer: engine
authority: P2
audience: developer
---

# Phase 5 Readiness Gate: Entry Criteria

## 1. Compliance Checklist
The following criteria must be met before any Phase 5 gameplay expansion logic is merged.

| Criterion | Requirement | Verification | status |
| :--- | :--- | :--- | :--- |
| **Movement Parity** | Must be in standard proof path. | `test_movement_parity.py` | [x] |
| **Interaction Parity**| Initial differential proof exists. | `test_resource_interaction_parity.py` | [x] |
| **Release Truth** | Manifest and docs are in-sync. | `manifest.json` | [x] |
| **Support Boundary** | Explicit movement/interaction scope.| `parity_exit_package.md` | [x] |
| **Contract Closure** | No decorative/fake fields. | `resource_governor_contract.md` | [x] |

## 2. Decision Record: CPU Governance
> [!IMPORTANT]
> **NARROWED SCOPE**: Entering Phase 5, the Resource Engine officially NARROWED its CPU governance claim. CPU pressure measurement is supported, but active throttling is EXCLUDED until the governor substrate is further hardened.

## 3. Approval Statement
Phase 5 recovery of town resolution and integrated progression is authorized. The engine substrate is verified bit-identical for the supported Phase 4 surface.
