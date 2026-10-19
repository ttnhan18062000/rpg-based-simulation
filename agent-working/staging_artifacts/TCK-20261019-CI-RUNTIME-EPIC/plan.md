---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261019-CI-RUNTIME-EPIC
phase: open
date: 2026-10-19
tags: [testing, workflows, performance]
---

# Plan

Epic, scope only. The children are in `agent-working/tickets/todos/ci-runtime/SEQUENCE.md`:
1. xdist inside the existing critical-path jobs, after a shared-state audit. No net new jobs.
2. A warn-only job-runtime budget, with its baseline taken after child 1 and after the Ubuntu 26 shift.
3. Trim informational work off main pushes after consulting platform-planner and lead-planner (ubuntu). The full suite stays on main.

Every child PR is reviewed by lead-planner-u24, and child 3 also by lead-planner (ubuntu). Sequencing advice from lead-planner-u24 (2026-10-19) is folded in: the concurrency limit, the post-merge safety net, warn-only, and baseline timing.
