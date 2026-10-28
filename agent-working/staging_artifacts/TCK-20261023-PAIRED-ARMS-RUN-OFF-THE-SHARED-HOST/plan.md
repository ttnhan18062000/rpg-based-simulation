---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST
phase: open
date: 2026-10-26
tags: [testing, performance, determinism]
---

# TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST: plan

Files: .github/workflows/paired-arms.yml (new), tools/test_architecture/paired_arms.py (new), docs/plans/test_architecture/reference/paired_arms_off_host.md (new), tests/static/test_ci_paired_arms_workflow_shape.py (new), tests/unit/tools/test_paired_arms.py (new), the two workflow guards (add paired-arms.yml).
1. paired_arms.py: plan_matrix / step_slug, run_arm (paired's own functions), runner_identity, assemble (the refusals), CLI.
2. Workflow: plan -> arms (matrix) -> aggregate; dispatch only; concurrency paired-arms-${{ inputs.step }} not cancelling; pinned actions; inputs via env.
3. Tests: static shape (AC4), unit (plan, run_arm, assemble refusals = AC2 on fake artifacts).
Scope guards: paired.py and arm_child.py untouched and not stubbed; no CI gate; no pull_request/push; no ledger code until T1 is on main.
AC map: AC1 and AC5 open (need dispatch / rpg PR); AC2 assemble tests; AC3 cost.json carries wall and RSS (ledger row after T1); AC4 static test and the pin guard.
