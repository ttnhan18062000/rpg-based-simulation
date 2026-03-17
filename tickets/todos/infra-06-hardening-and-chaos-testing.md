# infra-06: Hardening and Chaos Testing

## Objective
Introduce Property-Based Testing and Fault Injection to rigorously validate the engine's determinism and stability under extreme, unscripted stress conditions.

## Rationale
As we embrace true concurrency, data-driven registries, and robust databases, traditional unit tests will frequently miss edge cases in state transitions. The single-writer engine must survive extreme conditions and chaotic worker failures without crashing or breaking determinism.

## Scope & Affected Systems
- **Target Files**: `tests/test_world.py`, `tests/test_combat.py`, `src/config.py`, `src/engine/worker_pool.py`.
- **Implementation Steps**:
  1. Add `hypothesis` and `pytest-randomly` to test requirements.
  2. Create a dedicated `tests/test_invariants.py` suite using Hypothesis `@given` decorators to fuzz entity generation, item stats, and combat resolution.
  3. Define system invariants (e.g., `HP >= 0`, `Inventory Weight <= Max Capacity`, `Replay Fingerprint Holds`, `No Entity Duplication`).
  4. Extend `SimulationConfig` with a `chaos_mode` toggle and related fault-injection probabilities (e.g., `worker_drop_rate=0.01`).
  5. Instrument `WorkerPool` and `ActionQueue` to purposely drop or corrupt proposals when `chaos_mode` is active, proving the engine degrades gracefully instead of crashing.

## Dependencies
- Non-blocking. Excellent task to complete in parallel with epic-19 or epic-18.

## Acceptance Criteria
- `test_invariants.py` runs successfully against `Hypothesis` permutations.
- Fast, safe integration into the existing `make test` pipeline.
