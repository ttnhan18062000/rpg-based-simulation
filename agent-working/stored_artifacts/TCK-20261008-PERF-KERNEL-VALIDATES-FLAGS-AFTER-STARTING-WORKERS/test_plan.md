---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS
tags: []
---

# test_plan - TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS

tests/unit/engine/test_kernel_rejects_a_forbidden_flag_before_starting_any_worker.py: each of FORCE_NORMAL, BYPASS_GOVERNOR, DISABLE_RESOURCE_CEILINGS raises ConfigValidationError through Kernel(...) with no drain worker, no extra thread and no run folder (3 fail on main, pass with the fix); ordinary flags still start and cleanly stop the workers (1). Hash check: frontier_living_world s42 300t, final hash identical before and after.
