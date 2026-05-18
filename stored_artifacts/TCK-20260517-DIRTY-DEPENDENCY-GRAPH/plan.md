# Implementation Plan: Dirty Dependency Graph

## Objective

Implement `DirtyDependencyGraph` in `src/core/dirty.py` to formalize derived dirtiness across simulation domains and guarantee all pipeline phases operate on causally complete dirty sets.

## Proposed Changes

### Core Infrastructure

#### [MODIFY] [dirty.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/dirty.py)

1. Implement `DirtyDependencyGraph` class with `@staticmethod def expand(dirty: DirtySet) -> DirtySet`.
   - Propagate `movement_entities` -> `strategic_entities`, `social_entities`.
   - Propagate `inventory_entities` -> `strategic_entities`.
   - Propagate `combat_entities` -> `lifecycle_entities`, `social_entities`, `strategic_entities`.
   - Propagate `biological_entities` | `attribute_entities` -> `strategic_entities`, `lifecycle_entities`.
2. Update `DirtySetBuilder.build()` to return `DirtyDependencyGraph.expand(ds)`.
3. Update `DirtySet.from_update()` to return `DirtyDependencyGraph.expand(ds)`.

### Tests

#### [NEW] [test_dirty_dependency_graph.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/optimization/test_dirty_dependency_graph.py)

Implement comprehensive unit test suite covering:
- Causal propagation across all defined rules.
- Idempotency verification (`expand(expand(d)) == expand(d)`).
- Determinism verification (sorted output consistency).

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/optimization/test_dirty_dependency_graph.py -v`.
- Run `pytest tests/unit/ -m "not slow" -v` to ensure zero regressions across the codebase.
- Run `pytest tests/perf/test_dirty_parity.py -v` to verify parity and determinism under simulation load.
