---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING
artifact_type: plan
tags: [architecture, delivery]
---

# Plan — TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING

Written together with `TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING` (same batch, same job, two small flips); each
ticket still gets its own commit. Depends on ticket 1 (`666a8040e`, `94aba2578`): the job-level `continue-on-error` is gone, so removing the step's now matters.

## Approach
1. `.github/workflows/test.yml`: remove `continue-on-error: true` from the `Package registry` step; rewrite its comment (blocking since this ticket; exit 1 = a tracked top-level `src/` package with no row or a row for a missing package, or a schema problem; exit 2 = could not run; both fail the `Code health` job, which is already a required check, so no separate setting is needed). The only tolerated step left in the job is "Paths this PR changed".
2. `tests/codebase/test_package_registry.py`: the real-repo test `test_committed_registry_loads_and_is_schema_valid` gains the completeness assertion (`load_rows(..., (SCHEMA, COMPLETENESS))` against the live tree), and the module docstring is rewritten (a live-repo completeness test in a blocking lane is the second enforcement point, intended at the flip; review-checklist rule). `test_ci_step_is_advisory_in_the_code_health_job` becomes `test_ci_step_is_blocking_in_the_code_health_job` (no `continue-on-error`).
3. `tests/static/test_ci_uv_install.py`: the tolerant-step set becomes `{"Paths this PR changed"}`.
4. Docs: standard rule M5 cell "(advisory)" to blocking; environment guide gets one sentence (the `Package registry` step of `Code health` is blocking); the CI comment above the job lists it.
5. Soak review: new section in `docs/plans/codebase_health/python_code_craft_structure_soak_review.md` (window 2026-10-04 to 10-18): runs of the step, completeness/schema problems reported, false positives, whether the 36 registry rows were reviewed. Drafted now, finalized after 2026-10-18.
6. Live demo (owner-authorized push, throwaway draft PR, never merged): add `src/zz_flip_demo/__init__.py` with no row, `Code health` fails on `Package registry`; add the row, it passes. Record run links.
7. Announcement text for the planner: a PR that adds a top-level `src/` package without a row fails.

## Scope guards
No `src/` file in the merged diff (the demo branch is throwaway). No registry row changes. Nothing else in the job changes.

## Acceptance-criteria map
Dates: ticket Assumptions. Soak review: step 5. Fail/pass on real PR runs: step 6. Required-check setting: covered by `Code health` (recorded). No `src/`: `git diff --stat origin/main...HEAD`.
