---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261009-UBUNTU-26-RUNNER-PRECHECK
phase: open
date: 2026-10-09
tags: [architecture, delivery]
---

# plan — TCK-20261009-UBUNTU-26-RUNNER-PRECHECK

Planner decisions (codebase-planner, owner-approved 2026-10-09):
1. Measure first, pin only what needs it: a blanket pin only buys time and needs an exit date.
2. Probe = throwaway branch `ci-runner-26-probe`, `test.yml` `runs-on` only, never merged, closed afterwards; push and draft PR only after an owner yes.
3. Per-job comparison against main's run on the same base; skipped jobs are "not checked", not passes; advisory jobs are read by summary/annotations.
4. Deliverable is `docs/plans/codebase_health/ubuntu_26_runner_precheck.md`; a pin is a recommendation, not a change in this batch.
Scope guard: no `src/`, no `tests/`, no workflow edits on the batch branch.
