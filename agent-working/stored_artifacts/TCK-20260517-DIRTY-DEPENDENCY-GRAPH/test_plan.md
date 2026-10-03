---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260517-DIRTY-DEPENDENCY-GRAPH
artifact_type: test_plan
tags: [dirty, dependency, graph]
---

# Test Plan: Dirty Dependency Graph

## Automated Verification

1. **Unit Verification**:
   ```bash
   pytest tests/unit/optimization/test_dirty_dependency_graph.py -v
   ```
   Ensures exact correct propagation, determinism, and idempotency.

2. **Full Fast Regression Suite**:
   ```bash
   pytest tests/unit/ -m "not slow" -v
   ```
   Ensures seamless integration across all 17 simulation phases.

3. **Parity & Determinism Suite**:
   ```bash
   pytest tests/perf/test_dirty_parity.py -v
   ```
   Confirms bit-identical determinism under live simulation ticks.
