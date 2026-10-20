---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE
artifact_type: plan
date: 2026-10-20
tags: [testing, regression, simulation-quality]
---

# Plan — TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE

1. Format doc: "Kernel positives" (rule, what counts, the map, the lint, the process).
2. `tests/simulation_quality/rpg_gate/kernel_positives.yaml` with rpg's node ids for V1-V8.
3. `tests/architecture/test_rpg_gate_validity_rows_have_kernel_positives.py`: the lint plus regression cases.
4. Close the ticket in the PR; rpg-planner confirms the node ids (AC4).
