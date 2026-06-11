---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260517-STATIC-DIRTYSET-GUARD
artifact_type: test_plan
tags: [static, dirtyset, guard]
---

# Test Plan: Static Guard Against Direct DirtySet Usage

## Automated Test Execution

1. **Target Static Verification**:
   ```bash
   pytest tests/static/test_no_direct_dirtyset_candidate_selection.py -v
   ```
   Ensures that no file in `src/engine/pipeline_phases/`, `src/systems/`, or `src/ai/` directly references `dirty_set`.

2. **Full Fast Regression Suite**:
   ```bash
   pytest tests/unit/ -m "not slow" -v
   ```
   Ensures complete architectural and test stability across the entire project.

3. **Parity Check**:
   ```bash
   pytest tests/perf/test_dirty_parity.py -v
   ```
