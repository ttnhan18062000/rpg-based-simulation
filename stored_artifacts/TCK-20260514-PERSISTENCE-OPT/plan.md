# Implementation Plan: Persistence Layer Optimization (get_hash)

Optimize the `CanonicalStateHasher` to reduce the time spent in the persistence phase from ~230ms to < 50ms for 1,000 entities.

## Proposed Changes

### Engine Checkpoint Logic

#### [MODIFY] [checkpoint.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/checkpoint.py)
- Refactor `to_canonical_data` to avoid `asdict()` on entity components.
- Implement manual dictionary construction for:
    - `InteractionComponent`
    - `IdentityComponent` (including personality)
    - `AttributeComponent`
    - `AptitudeComponent`
    - `CombatComponent`
    - `BiologicalComponent`
    - `LifecycleComponent`
- Optimize nested loops and sorting.

### Core State Logic

#### [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- **Component Caching**:
    - Add `_canonical_cache: Dict[str, Any]` to each component dataclass (Interaction, Identity, etc.).
    - Since components are immutable in the read-only view, we can cache their canonical dictionary representation.
    - This allows $O(1)$ hashing for any component that hasn't changed.

## Verification Plan

### Automated Tests
- **Parity Test**: Create a script that compares the output of the new optimized hasher against the legacy `asdict()`-based output for a variety of states.
- **Benchmark**: Use `scripts/profile_engine.py` to verify the cumulative time reduction.
- **Regression**: Run existing integration tests to ensure replay still works.

### Manual Verification
- Inspect the generated hashes for bit-identical matches.
