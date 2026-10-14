---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-PERFBUDGET-RETIRE
date: 2026-10-11
tags: [performance, testing, regression]
---

# Plan: TCK-20261010-PERF-M2-PERFBUDGET-RETIRE

Pre-planned by perf-planner (dispatch 2026-10-10 after the owner's decision in `performance_contract.md` §5.2). Written at close.

## Order
1. `git grep` every reference (the ticket's list was incomplete), then delete `perf_baselines.json`, `tools/perf_guard.py`, `tests/unit/perf/test_perf_guard.py`.
2. `tests/perf/conftest.py`: remove `PerfBudget`, its loader and the `perf_budget` fixture, and the imports they leave unused.
3. `Makefile`, the repo-root allowlist (guideline and its test), `docs/testing/test_taxonomy.md` §4, the perf docs that describe the store as present.
4. `registries/session_roles.yaml` plus the generated role cards, after the owner confirmed the literal diff.

## Decisions where the ticket left a choice
- **The two "budget tests" are left unchanged.** They never used the fixture (they call `assert_perf_threshold` directly and already report softly), so there was nothing to convert.
- **The registry edit is in this PR, not held.** perf-planner said to put the diff in the PR body for the owner to confirm. Deleting the files breaks `test_real_registry_validates` (the perf seat's `owns` names them), so the PR cannot be green without it. I asked the owner directly with the literal diff; the owner said to include it.
- **`docs/testing/test_taxonomy.md` section 4 is rewritten, not deleted**, for what exists now (`perf_harness`, `assert_perf_threshold`, the tripwire, `baseline_lifecycle`). The `PERF_HARDWARE_CLASS` variable and the tolerance bands are removed: nothing read them any more.
- **Records and historical evidence are left as written**: the clause inventory, the `docs/plans/**` proposals and `experiments/**` describe the repository as it was; the invalidation ledger, the schema doc, the decisions record and contract §5.2 are updated, because they describe the present.
