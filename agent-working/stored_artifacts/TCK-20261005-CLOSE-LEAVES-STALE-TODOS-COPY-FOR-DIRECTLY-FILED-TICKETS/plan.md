---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS
artifact_type: plan
tags: []
---

# Plan
Shapes 1 and 2 of the ticket (no governing-file edit):
1. `check_ticket_finalized` fails, naming the path, when a same-basename file survives under `agent-working/tickets/todos/` (recursive).
2. `record_hand_orchestrated_closure.remove_stale_active_copies` deletes the `todos/` and `inprogress/` copies of the closed ticket and prints each.
3. Shape 3 (CLAUDE.md "After Work" wording) is NOT done: the checker FAIL plus the closure-tool removal make the omission loud and automatic, so the wording needs no change.
4. Docs: `docs/guides/delivery_process.md`. The PR-time corpus test stays as the backstop (out of scope).
