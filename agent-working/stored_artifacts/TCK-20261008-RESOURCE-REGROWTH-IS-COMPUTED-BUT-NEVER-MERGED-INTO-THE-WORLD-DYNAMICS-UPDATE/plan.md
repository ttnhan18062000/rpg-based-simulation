---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261008-RESOURCE-REGROWTH-IS-COMPUTED-BUT-NEVER-MERGED-INTO-THE-WORLD-DYNAMICS-UPDATE
artifact_type: plan
tags: [ecology, economy, resource]
---

# Plan

1. In `resolve_dynamics`, replace `nodes_add=...` and `next_node_id_set=...` in the `update.replace(...)` with one `update = update.merge(ecology_update)`, so the regen and `RESOURCE_RECOVERED` are no longer dropped. The function gets one line shorter.
2. Add the wiring test file (real `Kernel` run plus the refine step).
3. Re-point TOWN-137 at the world-level test.
4. Measure the all-gatherer effect on a pinned 5-seed x 3-world matrix against main 753f98ea9; report, do not tune.
