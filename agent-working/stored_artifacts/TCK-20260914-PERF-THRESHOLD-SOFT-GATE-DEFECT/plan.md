---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT
date: 2026-10-04
tags: [performance, testing]
---

# Plan: TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT

Docs only. No `src/` or `tests/` edit. No `hard=True` flip.

1. Close the ticket as superseded (AC1, second branch): M4 candidates PERF-M4-T02, T07 and T10 own the migration.
2. In `performance_m4_baseline_gate_a_epic.md`: point the `perf_assertions.py` gap-table row and the
   "Confirmed field evidence" note at this disposition and the owner IDs, and record the default question as an
   open input.
3. AC2 is moot: no call site is hardened here, because the owner's gate rule forbids it until the gate lifts.
4. Move artifacts to stored_artifacts; close with `record_hand_orchestrated_closure.py`.
