---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261010-PERF-M2-PERFBUDGET-RETIRE
phase: done
date: 2026-10-10
tags: [performance, testing, regression]
---

# TCK-20261010-PERF-M2-PERFBUDGET-RETIRE

## Title
PERF-M2: Delete PerfBudget, perf_baselines.json and tools/perf_guard.py (contract §5.2 disposition)

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Owner decision 2026-10-10, on PERF-M2-T03 (#496): the `PerfBudget` fixture and `perf_baselines.json` are deleted, not absorbed into the contract. `entries` in `perf_baselines.json` is empty, so the budget compares nothing. The paired tripwire (`tools/perf/tripwire.py`) and the baseline lifecycle (`tools/perf/baseline_lifecycle.py`) now own regression detection and baselines, and `tools/perf_guard.py measure` is a third, unused baseline path. Delete it so only one path remains. `performance_contract.md` §5.2 records this disposition (landed with T03).

## Scope
- Delete `perf_baselines.json`, `tools/perf_guard.py` and `tests/unit/perf/test_perf_guard.py`
- Remove the `perf_budget` / `PerfBudget` fixture from `tests/perf/conftest.py`, and change its two users (`tests/perf/test_phase2_self_model_budget.py`, `tests/perf/test_phase3_adventure_decision_budget.py`) so their measurements are reported but not budgeted (soft, like the other smoke bounds), or route them through `compare()` if that is a small change
- Remove the `perf-measure` Makefile target and its `.PHONY` entry
- Remove `perf_baselines.json` / `perf_guard.py` from `tests/codebase/test_repo_root_allowlist.py` and any scope map, inventory or doc that names them (`git grep`)
- Remove `perf_baselines.json` and `tools/perf_guard.py` from the perf domain's `owns` list in `registries/session_roles.yaml` (governing file: the owner confirms the literal diff)

## Out of Scope
- Any `src/` change (`src/perf/regression_gate.py` retires under its own lift)
- The 56 absolute-ms ceilings (`assert_perf_threshold` / `perf_check`): they stay as soft smoke bounds (owner decision 2026-10-10)
- Making any check blocking (OD-8)

## Acceptance Criteria
- [x] `git grep -n "perf_guard\|perf_baselines.json\|PerfBudget\|perf_budget"` outside `agent-working/` and historical docs returns nothing live
- [x] `tests/perf/test_phase2_self_model_budget.py` and `test_phase3_adventure_decision_budget.py` still run and still report their measurement; neither becomes blocking
- [x] `make help` no longer lists `perf-measure`, and the Makefile parses
- [x] `tests/codebase/test_repo_root_allowlist.py` and the tools-orphan check pass
- [x] The ticket's git diff touches no file under `src/`

## Related Tickets
- TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED
- TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
- TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

## Related Docs
- docs/engine/performance_contract.md §5.2
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261010-PERF-M2-PERFBUDGET-RETIRE/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- tools/perf_guard.py, perf_baselines.json, tests/perf/conftest.py, tests/unit/perf/test_perf_guard.py, Makefile, tests/codebase/test_repo_root_allowlist.py, registries/session_roles.yaml

## Assumptions / Open Questions
- Owners outside perf (route.py): `Makefile` (lead-planner, stack root), `tests/perf/conftest.py` and the two budget tests (shared with rpg-planner), `tests/codebase/**` (check with route.py). Name each in the PR body.
- Lands after T03 (#496), so that §5.2 already records the disposition.

## Implementation Notes
- Plan, investigation and test plan: `agent-working/stored_artifacts/TCK-20261010-PERF-M2-PERFBUDGET-RETIRE/`.
- **Two premises of the ticket were wrong, and are corrected.** (1) The two budget tests do not use the `perf_budget` fixture (the name appears only in their function names); no test used it, so they are unchanged. `performance_contract.md` §5.2 had repeated "two users" (from my T03 edit); it now says so. (2) The reference list was incomplete: also the repo-root allowlist guideline, `docs/testing/test_taxonomy.md` §4 (rewritten), and the two generated role cards.
- **The registry edit is in this PR on the owner's confirmation.** Deleting the files makes `test_real_registry_validates` fail (the perf seat's `owns` names them), so the PR cannot be green without it. The owner confirmed the literal diff: remove `tools/perf_guard.py` and `perf_baselines.json` from the perf seat's `owns` in `registries/session_roles.yaml` (owner of that file: agent-working-planner), and regenerate the two role cards with `python3 -m tools.sessions.generate_agents`.
- The repo-root allowlist parser reads backticked names, so the guideline's explanatory sentence does not name the deleted file in backticks.
- **A process mistake, caught before any push:** my first `git add` named a path that no longer existed, which aborts the whole command, so the first commit held only the three deletions while its message described much more. A clean-worktree run showed the old registry and test still committed. I squashed the two unpushed commits and recommitted with `git add -u`.
- The session drift test times out in my cluttered worktree (about 32,000 untracked files) and passes in a clean one.

## Test Summary
- In a **clean worktree of the commit** (16,154 tracked files): `tests/tools/test_session_agent_generator.py`, `test_session_roster.py`, `test_session_cards.py`, `test_session_boundary.py`, `test_session_launch.py`, `tests/codebase/test_repo_root_allowlist.py`, `tests/tools/test_agent_working_paths_guard.py`, `tests/tools/test_test_scope_coverage_static.py`, `tests/unit/perf`, and the two budget tests: **394 passed**.
- `make help` lists no `perf-measure` and the Makefile parses; the tools orphan check does not list `tools/perf_guard.py`; the diff has no `src/` path.
- Not run: the full suite; CI (pushed after this).

## Files Changed
- Deleted: `perf_baselines.json`, `tools/perf_guard.py`, `tests/unit/perf/test_perf_guard.py`.
- Edited: `tests/perf/conftest.py`, `Makefile`, `docs/guidelines/repo_tooling_layout.md`, `tests/codebase/test_repo_root_allowlist.py`, `registries/session_roles.yaml`, `.claude/agents/session-perf-implementer.md` and `session-perf-planner.md` (generated), `docs/testing/test_taxonomy.md`, `docs/engine/performance_contract.md` (§5.2), `docs/architecture/performance_optimization_decisions.md`, `docs/performance/baseline_invalidation_ledger.md`, `docs/performance/benchmark_identity_schema.md`.
- Tickets and artifacts: this ticket and `agent-working/stored_artifacts/TCK-20261010-PERF-M2-PERFBUDGET-RETIRE/`.

## Completion Summary
The per-test PerfBudget store is gone: `perf_baselines.json`, `tools/perf_guard.py`, its tests, the `perf_budget` fixture and the `make perf-measure` target are deleted, and regression detection and baselines belong to `tools/perf/tripwire.py` and `tools/perf/baseline_lifecycle.py` alone. Nothing live names the store; the remaining mentions record the deletion or are historical evidence. The registry and role-card edit went in on the owner's confirmation. Left open: nothing from this ticket; the 56 absolute-ms ceilings stay as soft smoke bounds by the owner's decision, and `src/perf/regression_gate.py` retires under its own later lift.
