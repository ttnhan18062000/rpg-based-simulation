---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [infra_06]
---

# Phase E: Property-Based Fuzzing (Hardening)

## Objective
Use automated fuzzing to find "impossible" edge cases in our core math and state transitions.

## Implementation Details
1. **Tooling**: Integrate `Hypothesis` into our `pytest` suite.
2. **Invariants**:
    - `HP` must never be less than 0 or greater than `MAX_HP`.
    - `determinism_hash` must be identical regardless of execution environment.
    - `SpeedDelay` must always be between 0.1s and 10.0s.
3. **Strategies**:
    - Build a strategy to generate random `Entity` objects with weird combinations of `Attributes` and `Traits`.
    - Build a strategy to generate random `ActionProposals`.

## Success Criteria
- Identifying at least one "divide by zero" or "floating point error" in current derived stat logic.
- All core engine tests pass with 100+ random permutations per test.
