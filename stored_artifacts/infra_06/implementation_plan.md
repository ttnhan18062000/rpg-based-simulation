---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [infra_06]
---

# Implementation Plan: Infra-06 (Hardening & Chaos Testing)

## 1. Objective & Rationale

Validate the engine's resilience against distributed failures and edge-case state transitions. We must ensure that **Determinism** is maintained even when external components (AI Workers, Network) behave chaotically.

### Rationale:
- **Scalability**: As we move to 100+ entities with distributed AI, the surface area for "soft failures" increases exponentially.
- **Reliability**: Long-term world progression (Epic-17) requires an engine that can recover from a "dropped brain result" without a tick-cycle stall.

---

## 2. Comparative Logic Shift

### Current Behavior (Reactive)
- **Unit Tests**: Scenario-based (specific inputs -> specific outputs).
- **Worker Trust**: `WorldLoop` expects all active entities to return a decision. A missing decision can lead to timing issues or state inconsistencies.
- **Stability**: Relies on "happy path" assumptions for attribute values and combat math.

### New Behavior (Proactive Hardening)
1. **Property-Based Invariants**: 
    - *Logic*: Shift from scenario-testing to invariant-testing using **Hypothesis**.
    - *Outcome*: Guarantees that no matter the input range (Speed 0.1 to 10,000), the `speed_delay` calculation never returns `NaN` or `Inf`.
2. **Graceful Fallbacks**:
    - *Logic*: Implement a `default_proposal` (IDLE) for any entity that fails to return a result within the timeout.
    - *Outcome*: The simulation timeline continues even if 10% of workers are offline.
3. **Chaos Mode**:
    - *Logic*: Intentional fault injection at the `WorkerPool` layer.
    - *Outcome*: Continuous verification that "dropped packets" don't break determinism in the `Snapshot` history.

---

## 3. Technical Roadmap

### Phase E: Property-Based Fuzzing
- **Target**: `tests/test_invariants.py`.
- **Logic**: Use `@given` strategies to fuzz `Entity` generation. Validate that derived stats (MAX_HP, ATK) always stay within logical bounds.

### Phase F: Fault Injection & Worker Grace
- **Target**: `src/engine/worker_pool.py` and `src/config.py`.
- **Logic**: Add `chaos_mode` with a `drop_rate` probability. Ensure `WorldLoop` can successfully resolve a tick where 1 or more entities have missing AI results.

---

## 4. Verification Plan
- **Stress Test**: Run 10k ticks with `chaos_mode: true` and `drop_rate: 0.05`. Verify that the replay fingerprint still matches a second run with the same seed (determinism despite drops).
- **Hypothesis Reports**: Zero failures found across 1,000+ random permutations of the `Combat` and `Attribute` systems.
