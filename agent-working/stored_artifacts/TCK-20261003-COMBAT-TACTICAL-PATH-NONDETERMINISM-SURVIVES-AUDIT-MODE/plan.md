---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE
artifact_type: plan
tags: [engine, combat, determinism, root-cause]
---

# Plan: confirm-or-refute first, characterise, do not fix

The ticket's own instruction is "start with a confirm-or-refute probe, not a fix", and the planner's dispatch
said to re-measure before root-causing and to stop and report if the cause outgrew the batch.

1. Re-measure on the current tree with the canonical hasher and a different-seed positive control.
2. If it persists, find the first divergent tick and the diverging fields.
3. Narrow to the smallest bounded mechanism the evidence supports, one probe at a time, with a stop condition at
   each step.
4. Record the verdict (distinct from `INFRA-273`), the row-7 class, and the doc contradiction; leave the fix to a
   separate ticket because the candidate sits on the contested surface (`src/core/dirty.py`).

Scope guards: no source change; the exclusive hold on `kernel.py` and `governor.py` was not used; the
`deterministic_execution.md` correction is not made here (it is in the new fix ticket).
