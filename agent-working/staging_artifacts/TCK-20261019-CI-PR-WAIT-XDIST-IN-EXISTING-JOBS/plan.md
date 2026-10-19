---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS
artifact_type: plan
date: 2026-10-19
tags: [testing, workflows, performance]
---

# Plan — TCK-20261019-CI-PR-WAIT-XDIST-IN-EXISTING-JOBS

1. Audit (investigation.md) before any workflow change: done.
2. `pytest-xdist` in the dev group, locked (`uv add --dev`).
3. test.yml: `-n auto --dist loadgroup` on Integration, Tools f–z and the API job's directory steps; visual_assets split into a parallel step (three `--ignore`) and a serial store-lock step; merge both JUnit files; Aseprite note after the merge; base-branch collect step lists the same paths.
4. Pins: update the two step-name and path-set pins in `tests/tools/test_ci_split_tools_jobs.py` for the serial step; add `tests/static/test_ci_xdist_in_critical_path_jobs.py` (flags, job count, serial step, JUnit merge, dependency).
5. fyi to agent-working-planner before Tools f–z (sent, replied). Rebase onto #647 if it lands first.
6. PR; three consecutive CI runs per job by re-run; medians against the baseline; lead-planner-u24 comment review.

Scope guards: no job added, no marker, deselection or selection changed, slow lane and other workflows untouched.
