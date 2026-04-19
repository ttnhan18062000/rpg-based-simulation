# Test Plan: Authoritative Mutation Audit

## Objective
Prove that the authoritative state is immutable, isolated from observational paths, and that all mutations flow exclusively through the `ApplyPath`.

## Automated Tests

### 1. Prior-State Purity Test (`test_prior_state_purity`)
- **Input**: An `AuthoritativeState` (Generation N) and a `StateUpdate`.
- **Action**: Call `ApplyPath.apply_generation` to produce Generation N+1.
- **Assertion**:
    - Generation N+1 contains the updates.
    - Generation N is UNCHANGED.
    - Capturing the hash of Generation N before and after the apply must yield the same result.

### 2. Anti-Aliasing Test (`test_no_hidden_mutation`)
- **Input**: An `AuthoritativeState` with an entity having property `{"damage": 10}`.
- **Action**: 
    - Simulate the `Kernel` passing the entity to a worker.
    - The worker (maliciously or accidentally) does `entity.properties["damage"] = 99`.
- **Assertion**: Verifying `kernel.state.entities[id].properties["damage"]` is still `10`.

### 3. Singular Mutation Audit
- **Action**: Grep for any code that calls `dataclasses.replace` on `AuthoritativeState` or `EntityState` outside of `src_v2/engine/apply.py`.
- **Expected**: Only `apply.py` should perform authoritative transitions.

### 4. Deterministic Apply Order
- **Input**: A `StateUpdate` with entity updates in random order.
- **Action**: Call `apply_generation` twice with different update ordering.
- **Assertion**: The resulting state generations must have identical hashes.

## Manual Verification
- Review all usages of `replace` for `AuthoritativeState` to ensure they are constrained to the apply path.
