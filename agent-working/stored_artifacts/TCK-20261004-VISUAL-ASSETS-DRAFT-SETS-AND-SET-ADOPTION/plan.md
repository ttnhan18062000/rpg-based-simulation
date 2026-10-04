---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION
artifact_type: plan
tags: [architecture, mcp, testing]
---

# Plan — TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION

1. Contracts `DraftSet`, `SetAdoptionRecord`; measure the widest records (stop and tell the planner if over the bound).
2. Extract `adopt`'s shared checks; `drafts.py` (keep, verify, the chain check); `setadoption.py`; CLI; catalog verify for set records.
3. Tests incl. one per chain link and a render-comparison mutant; docs, ADR D12, budgets row.
