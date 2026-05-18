# Investigation: Resource-Safe Engine Milestone 2

## Goal
Implement the core execution logic for the minimal deterministic kernel.

## Architectural Decisions

### 1. Passive vs Active Separation
- **Passive World Time**: Will be handled in the `INIT` or `ADVANCEMENT` phase. It affects global state (e.g., world-clock, weather transitions) regardless of entity activity.
- **Active Entity Action**: Handled in `COLLECTION` and `RESOLUTION`. Gated by a `ReadinessEvaluator`.

### 2. The Apply Path
- To ensure determinism and avoid hidden mutations, every change to `AuthoritativeState` must be bundled into a `StateUpdate` collection.
- The `RESOLUTION` phase is the singular authority that iterates over these updates and applies them to a new state generation.

### 3. Checkpoint Hashing
- We need a `CanonicalStateHasher`.
- Since `AuthoritativeState` uses standard dataclasses and dicts, we can:
  1. Convert to a sorted dict.
  2. Map Enums to values.
  3. Serialize to JSON.
  4. Hash the resulting string.

### 4. Deterministic Tie-Breaking
- If two entities act at the same tick, we use `entity_id` as the primary tie-breaker for application order.

## Technical Risks
- **Iteration Order**: Python dicts (3.7+) maintain insertion order, but relying on this is risky for determinism across different environments.
- **Solution**: Explicitly sort entity IDs and resource keys during hashing and phase processing.
- **Floating Point Drift**: Different hardware/OS can produce tiny drifts in FP math.
- **Solution**: For Milestone 2, we will stick to basic arithmetic and avoid complex math (sin/cos/exp) until we implement a fixed-point or cross-platform math wrapper.

## Readiness Mechanics
- We'll use a `ReadinessThreshold` (e.g., 100.0).
- Every tick, entities gain `readiness_speed`.
- If `readiness >= 100.0`, they are eligible for the `COLLECTION` phase.
