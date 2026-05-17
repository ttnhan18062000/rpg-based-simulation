# TCK-20260517-DIRTY-DEPENDENCY-GRAPH

## Title

Dirty Dependency Graph Implementation

## Status

DONE

## Request Summary

Implement Milestone 4 of the Performance Optimization Hardening Plan: `DirtyDependencyGraph`, an explicit mechanism that expands direct domain dirtiness (e.g. movement) into derived downstream dirtiness (e.g. strategic, social, lifecycle). Integrate this directly into `DirtySetBuilder.build()` and `DirtySet.from_update()` to ensure all simulation phases operate on fully expanded, causally correct dirty sets while maintaining strict determinism and idempotency.

## Scope

- Implement `DirtyDependencyGraph` class with `@staticmethod def expand(dirty: DirtySet) -> DirtySet` in `src/core/dirty.py`.
- Define explicit causal expansion rules:
  - Movement -> Strategic, Social
  - Inventory -> Strategic
  - Combat -> Lifecycle, Social, Strategic
  - Biological / Attributes -> Strategic, Lifecycle
- Integrate `DirtyDependencyGraph.expand()` into `DirtySetBuilder.build()`, `DirtySet.from_update()`, and `DirtySet.merge()`.
- Implement unit test suite in `tests/unit/optimization/test_dirty_dependency_graph.py` verifying determinism, idempotency, and correct domain expansions.

## Out of Scope

- Modifying downstream simulation phases beyond providing the fully expanded dirty sets.

## Acceptance Criteria

- Dependency rules are explicit and centralized in `DirtyDependencyGraph`.
- `expand(dirty)` is 100% deterministic and idempotent (`expand(expand(dirty)) == expand(dirty)`).
- `tests/unit/optimization/test_dirty_dependency_graph.py` passes successfully.
- Full unit test suite passes with zero regressions.

## Related Tickets

- Milestone 1: CandidateSelector (`TCK-20260517-CANDIDATE-SELECTOR.md`)
- Milestone 2: Full-Scan Compliance (`TCK-20260517-FULL-SCAN-COMPLIANCE.md`)
- Milestone 3: Static DirtySet Guard (`TCK-20260517-STATIC-DIRTYSET-GUARD.md`)

## Related Docs

- `perf_test_plan.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260517-DIRTY-DEPENDENCY-GRAPH/`

## Related Code Areas

- `src/core/dirty.py`
- `tests/unit/optimization/test_dirty_dependency_graph.py`

## Assumptions / Open Questions

- None.

## Implementation Notes

- Implemented centralized causal expansion mapping inside `DirtyDependencyGraph.expand()` and embedded it directly into `DirtySet.from_update()`, `DirtySet.merge()`, and `DirtySetBuilder.build()`.

## Test Summary

- `pytest tests/unit/optimization/test_dirty_dependency_graph.py -v` passed 6/6 tests in 0.07s.
- `pytest tests/perf/test_dirty_parity.py -v` passed 1/1 test in 20.51s, confirming bit-exact parity.
- `pytest tests/unit/ -m "not slow" -v` passed 743/743 tests in 12.56s without regressions.

## Files Changed

- `src/core/dirty.py`
- `tests/unit/optimization/test_dirty_dependency_graph.py`
- `perf_test_plan.md`

## Completion Summary

- Successfully established `DirtyDependencyGraph` as the centralized mechanism for deriving downstream simulation dependencies, guaranteeing that all pipeline phases operate on causally complete and idempotent dirty sets.
