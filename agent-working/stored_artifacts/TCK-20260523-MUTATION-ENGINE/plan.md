---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-ENGINE
artifact_type: plan
tags: [mutation, engine]
---

# Implementation Plan - Mutation Engine

## Objectives
- Create the `MutationEngine` class in `src/lab/mutation.py` to isolate and apply target mutations.
- Ensure strict non-in-place mutation.
- Support deep dot-notation paths and custom operations: `set`, `add`, `multiply`, `toggle`, `remove`, `duplicate`.
- Run full validation against mutated specs using Pydantic and validators.

## Proposed Changes
1. **`src/lab/mutation.py`**:
   - `MutationApplyReport`: schema to record each mutation application attempt.
   - `MutationEngine`: core mutation applicator and validator.
2. **`tests/unit/lab/test_mutation_engine.py`**:
   - Extensive unit test suite validating all 6 operations, error behaviors, immutability, and validator barriers.

## Verification
- Target test suite execution via `pytest`.
