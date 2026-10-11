---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261010-PERF-M2-PERFBUDGET-RETIRE
phase: open
date: 2026-10-10
tags: [performance, testing, regression]
---

# TCK-20261010-PERF-M2-PERFBUDGET-RETIRE

## Title
PERF-M2: Delete PerfBudget, perf_baselines.json and tools/perf_guard.py (contract §5.2 disposition)

## Status
OPEN

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
- [ ] `git grep -n "perf_guard\|perf_baselines.json\|PerfBudget\|perf_budget"` outside `agent-working/` and historical docs returns nothing live
- [ ] `tests/perf/test_phase2_self_model_budget.py` and `test_phase3_adventure_decision_budget.py` still run and still report their measurement; neither becomes blocking
- [ ] `make help` no longer lists `perf-measure`, and the Makefile parses
- [ ] `tests/codebase/test_repo_root_allowlist.py` and the tools-orphan check pass
- [ ] The ticket's git diff touches no file under `src/`

## Related Tickets
- TCK-20261010-PERF-M2-T03-TRIPWIRE-PAIRED
- TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
- TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

## Related Docs
- docs/engine/performance_contract.md §5.2
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/perf_guard.py, perf_baselines.json, tests/perf/conftest.py, tests/unit/perf/test_perf_guard.py, Makefile, tests/codebase/test_repo_root_allowlist.py, registries/session_roles.yaml

## Assumptions / Open Questions
- Owners outside perf (route.py): `Makefile` (lead-planner, stack root), `tests/perf/conftest.py` and the two budget tests (shared with rpg-planner), `tests/codebase/**` (check with route.py). Name each in the PR body.
- Lands after T03 (#496), so that §5.2 already records the disposition.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
