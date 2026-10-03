---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261003-PERF-PROFILING-TOOLKIT
date: 2026-10-03
tags: [performance]
---

# Plan: TCK-20261003-PERF-PROFILING-TOOLKIT

## Summary
Tooling only: `tools/perf/profile_tick.py`, `profile_diff.py`, `flag_attribution.py` plus the shared
`_profiling_common.py`, tests, a guide, and an optional `perf` dependency group for py-spy. No `src/`
edit, no baseline, no gate, nothing generated is committed.

## Steps
1. Read `profile_engine.py`, the scenario builders, the feature-flag manager and how the kernel merges flags.
2. Confirm py-spy can sample a child process in this sandbox (it can; installed to a scratch dir, not the repo).
3. Write the common helpers (header, statistics, folded-stack parsing and diffing, attribution arithmetic).
4. Write the three tools; run each against the real kernel at small entity counts.
5. Tests that need no profiler binary; one end-to-end test that skips without py-spy.
6. Guide, `perf` group, scope-map entries; send one real output of each tool to perf-planner; close after review.

## Scope guards
No `src/` edit. py-spy only in the optional `perf` group (not `requirements.txt`, not CI). If py-spy had
been unable to sample here the work would have stopped with the exact error; it was able to.
`.claude/agents/test-scoper.md` is not touched (known follow-up from the earlier tickets).

## Acceptance-criteria map
AC1 -> pyproject `perf` group, requirements.txt untouched; AC2 -> real `profile_tick` run (test plan);
AC3 -> `profile_diff` on two real folded files; AC4 -> real `flag_attribution` run; AC5 -> metropolis warning
tests; AC6 -> clean `git status` after the real runs; AC7 -> tests with the binary absent; AC8 -> guide;
AC9 -> diff scope.
