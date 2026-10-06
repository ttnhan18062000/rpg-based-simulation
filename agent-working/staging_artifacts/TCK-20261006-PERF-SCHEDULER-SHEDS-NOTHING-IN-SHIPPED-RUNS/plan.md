---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS
date: 2026-10-07
tags: [performance, determinism, engine]
---

# Plan: TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS

Investigation and decision only; no `src/` edit.
1. Find every definition, doc, parity entry and test about periodic or sheddable work (grep over `src/`, `docs/`, `tests/`).
2. Read the git history of `PeriodicDefinition(` and `scheduler.py`.
3. Trace what each `GovernorPolicy` field changes (readers outside `policy.py`).
4. Check committed baselines and live readers of `dropped_work`.
5. Write the three options with costs and one recommendation; mark the decision as the owner's (pending).
6. Close the ticket (hand-orchestrated closure), after the planner's review.
