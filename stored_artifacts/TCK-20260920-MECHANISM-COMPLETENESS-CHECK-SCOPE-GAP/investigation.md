---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP
artifact_type: investigation
tags: [architecture]
---

# Investigation

- The ticket's 2026-09-20 figures did not reproduce. Under an explicit rule (see the checker) the start-of-batch numbers were: 295 files, 260 uncited, 102 unbound mechanism-shaped classes, 49 wired. The ticket's "14" corresponds to no rule tried (any-reference gives 73, cross-package file-level gives 40).
- Triage by three read-only investigators plus the RPG planner's identity calls: 16 bound, 12 registered as new mechanisms, 18 infrastructure exclusions, 3 pending (`PerceptionGate` held for the planner's perception-contract batch; two dead same-name twins routed to `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`).
- Runtime probe (positive-controlled per-method counters, 3 worlds x 1000 ticks) found 15 classes with 0 calls; the registrations for the zero-call ones use verdict `inconclusive`, not a claim of absence or of working.
- `strategy/capacity.py::CapacityService` was bound to `cognition_capacity_fatigue` after checking that the registry entry already documents it as the live twin.
- Not done, by decision: nothing registered for `progression/skills.py::SkillScalingService` (dead twin).
