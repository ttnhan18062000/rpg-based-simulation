---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260604-PHASE20-CONTRACT-AND-TESTMAP
artifact_type: test_plan
tags: [phase20, contract, and, testmap]
---

# Test Plan: Phase 20 Content Usage Contract

## Unit Tests
We will add `tests/unit/content/test_content_usage_matrix.py`.

### Test Cases
1. `test_matrix_existence_and_loading`:
   - Asserts that the Python matrix definition (`src/content/matrix.py`) can be imported.
   - Asserts that the generated markdown report file exists.
2. `test_matrix_completeness`:
   - Walks all files/directories in `data/content/` (excluding gitkeeps/raw files).
   - Verifies that every file/directory is mapped to a family in `ContentUsageMatrix`.
3. `test_matrix_validation`:
   - Verifies that every family in `ContentUsageMatrix` has:
     - schema class
     - validator coverage
     - resolver component or is explicitly marked design-only
     - compile/runtime consumer
     - exactly one implementation state defined.
4. `test_compatibility_constraints`:
   - Asserts that compatibility data (e.g. `compatibility/legacy_enemy_projection.yaml` or `spawn_tables.yaml`) cannot be marked `RUNTIME_AUTHORITATIVE`.
   - Asserts that core components (like `world/*`) cannot stay `LOADED_ONLY`.

## Verification Commands
- `pytest tests/unit/content/test_content_usage_matrix.py`
