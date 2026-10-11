---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-PERF-M2-PERFBUDGET-RETIRE
date: 2026-10-11
tags: [performance, testing, regression]
---

# Test plan: TCK-20261010-PERF-M2-PERFBUDGET-RETIRE

No new test: this ticket deletes. The proof is that the tests that guard the deleted things still pass in a clean worktree of the commit (394 passed): the session registry and cards, the repo-root allowlist, the paths guard, the scope-map tests, `tests/unit/perf`, and the two budget tests.

## Proof Plan

| Criterion | Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|---|
| Nothing live names the deleted store | static | check | the ticket's acceptance criteria | `git grep` leaves only records of the deletion and historical evidence | `git grep -n "perf_guard\|perf_baselines\|PerfBudget\|perf_budget\|perf-measure" -- . ':!agent-working' ':!docs/archive' ':!docs/plans' ':!experiments'` |
| The two budget tests still run and report | integration | regression | the ticket | they pass and stay soft | `pytest tests/perf/test_phase2_self_model_budget.py tests/perf/test_phase3_adventure_decision_budget.py` |
| `make help` has no `perf-measure`; the Makefile parses | static | check | the ticket | `make -n help` succeeds; no `perf-measure` line | `make help \| grep -c perf-measure` |
| The allowlist and the orphan check pass | integration | regression | the repo's guards | the tracked root equals the allowlist; `tools/perf_guard.py` is not listed | `pytest tests/codebase/test_repo_root_allowlist.py`; `python3 tools/gate_checks/tools_orphan_check.py` |
| The registry and the cards agree | integration | regression | `tools/sessions` | `test_real_registry_validates` and `test_committed_files_have_no_drift` pass **in a clean worktree** | `pytest tests/tools/test_session_roster.py tests/tools/test_session_agent_generator.py` |
| No `src/` change | static | diff check | OD-8 | no `src/` path in the diff | `git diff origin/main --name-only -- src` |

Not proven: the full suite; the CI run.
