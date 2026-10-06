---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-TEST-SPLIT-PINNED-NORMAL-WITH-HARD-PRECONDITIONS
artifact_type: plan
tags: [engine, combat]
---

# Plan

1. Add the optional `governor` argument to `ScenarioRuntimeService` and pass it to `Kernel` in `_build_kernel`.
2. Replace the combined test with: a pinned governor subclass, shared instrumentation (decision, router phase, router entry, tick), a module-scoped fixture with hard preconditions, and three tests.
3. Add the positive controls and the static single-SKILL-writer test; mutate the instrument to show the controls fail.
4. Run the slow tests at `--resource-budget large`, the other `ScenarioRuntimeService` tests, and the code-health gates in a scratch venv.
5. Update the campaign ticket, file the cooperation-share ticket, add the measured-contact criterion to the two fix tickets.
