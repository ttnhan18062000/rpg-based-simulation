---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
artifact_type: plan
tags: [core, bug]
---

# Plan (Scope step; implementation waits for rpg-planner's decisions)

1. Scan and classification recorded in investigation.md (done).
2. Report options and a recommendation to rpg-planner-ubuntu before committing any decision: which copy is authoritative per pair; whether each dead twin is deleted or kept with a reason; any test change; any ledger or registry change.
3. After the rulings: delete or re-export per decision; add the architecture guard (a test that scans `src/` for top-level classes defined in two modules, mechanism-shaped names must be in an allowlist with a stated reason, the other duplicate names are listed with a classification); update `WIDER_PENDING` and its pinned counts only as decided.
4. Gates: scoped tests, `tests/unit/tools` serially under MemoryMax=3G, `make code-health`, `make lint-imports`, one paired --neutral for the batch.
