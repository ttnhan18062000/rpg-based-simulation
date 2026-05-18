# Replacement Ledger Governance & Change Control

This document defines the formal rules for managing the [Authoritative Replacement Ledger](../engine/legacy_replacement_ledger.md) across all future phases of the engine transition.

## 1. Principle of Ledger Primacy
The ledger is the singular project artifact allowed to represent replacement truth. Narratives, tickets, and summaries must be derived from the ledger, never the inverse.

## 2. Change-Control Rules

| Activity | Requirement | Approval |
| :--- | :--- | :--- |
| **Adding a New Row** | Must prove the behavior existed in legacy `src` with a source/test link. | Technical Lead |
| **Correcting Evidence** | Must include a commit SHA or proof artifact representing the new truth. | Technical Lead |
| **Status Change** | Must provide a rationale for কেন/how the status shifted (e.g. implementation complete). | Milestone Owner |
| **Rationale Update** | Must be recorded in the `divergence_log.md` if the change implies a divergence. | Milestone Owner |
| **Phase Allocation Shift**| Must be justified by dependency or resource constraints in the backlog. | Project Lead |

## 3. Mandatory Artifact Updates
Any modification to the ledger must be accompanied by an update to:
- The [Maturity Snapshot](../engine/legacy_replacement_ledger.md) (Totals).
- The [Remaining Replacement Scope](../engine/remaining_replacement_scope.md) (if phase or count changes).
- The [Audit Log](../engine/legacy_replacement_ledger.md).

## 4. Constraint Enforcement
Planning for Phases 7 through 10 is formally constrained by this baseline. A feature cannot be declared "Supported" in a future phase unless its corresponding row in the ledger is marked as **SUPPORTED** with a linked **Proof Artifact**.
